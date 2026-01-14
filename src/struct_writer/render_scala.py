"""Scala code renderer for struct-writer."""

import logging
from pathlib import Path
from typing import Any

from struct_writer.definitions import (
    BitField,
    DefinedType,
    Enumeration,
    Group,
    Structure,
    TypeDefinitions,
)
from struct_writer.templating import Template

_logger = logging.getLogger(__name__)

rendered: set[str] = {"file"}

# Scala reserved keywords that need backtick escaping
SCALA_KEYWORDS = {
    "abstract", "case", "catch", "class", "def", "do", "else", "extends",
    "false", "final", "finally", "for", "forSome", "if", "implicit", "import",
    "lazy", "match", "new", "null", "object", "override", "package", "private",
    "protected", "return", "sealed", "super", "this", "throw", "trait", "true",
    "try", "type", "val", "var", "while", "with", "yield"
}


def escape_scala_keyword(name: str) -> str:
    """Escape Scala keywords with backticks."""
    return f"`{name}`" if name in SCALA_KEYWORDS else name


def format_large_int(value: int) -> str:
    """Format integer literal, adding L suffix for values > Int.MaxValue."""
    if value > 2147483647 or value < -2147483648:
        return f"{value}L"
    return str(value)


def render_file(
    definitions: dict[str, Any],
    templates: dict[str, Any],
    output_file: Path,
) -> str:
    """Render complete Scala file from definitions."""
    rendered.clear()
    rendered.add("file")

    parsed_definitions = TypeDefinitions.from_dict(definitions)

    # Extract package from output file path
    package = extract_package_from_path(output_file)

    s = ""
    s += Template(templates["file"]["description"]).safe_render(
        file=parsed_definitions.file_info
    )
    s += Template(templates["file"]["header"]).safe_render(
        out_file=output_file, package=package
    )
    s += render_definitions(parsed_definitions, templates)
    s += Template(templates["file"]["footer"]).safe_render(out_file=output_file)
    return s


def extract_package_from_path(output_file: Path) -> str:
    """Extract Scala package from file path (e.g., com.axon.thunderbird.generated)."""
    parts = output_file.parts
    try:
        # Look for scala/src/main/scala pattern
        if "scala" in parts:
            scala_idx = parts.index("scala")
            # Check for src/main/scala pattern after scala
            remaining = parts[scala_idx + 1 :]
            if len(remaining) >= 3 and remaining[:3] == ("src", "main", "scala"):
                package_parts = remaining[3:-1]  # Exclude the filename
                return ".".join(package_parts)
        # Look for just src/main/scala pattern
        if "src" in parts:
            src_idx = parts.index("src")
            remaining = parts[src_idx:]
            if len(remaining) >= 3 and remaining[:3] == ("src", "main", "scala"):
                package_parts = remaining[3:-1]  # Exclude the filename
                return ".".join(package_parts)
    except (ValueError, IndexError):
        pass
    return "generated"


def render_definitions(
    definitions: TypeDefinitions,
    templates: dict[str, Any],
) -> str:
    """Render all definitions."""
    s = ""
    element_names = sorted(definitions.definitions.keys())

    # Render groups first (they define the sealed traits that structures extend)
    group_names = {
        k for k, v in definitions.definitions.items() if isinstance(v, Group)
    }
    for element_name in group_names:
        s += render_definition(element_name, definitions.definitions, templates)

    # Render remaining definitions
    for element_name in element_names:
        s += render_definition(element_name, definitions.definitions, templates)
    return s


def render_definition(
    element_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
) -> str:
    """Render a single definition based on its type."""
    if element_name in rendered:
        return ""
    rendered.add(element_name)
    definition = definitions[element_name]
    s = ""
    if isinstance(definition, Structure):
        s += render_structure(element_name, definitions, templates)
    elif isinstance(definition, Enumeration):
        s += render_enum(element_name, definitions, templates)
    elif isinstance(definition, Group):
        s += render_group(element_name, definitions, templates)
    elif isinstance(definition, BitField):
        s += render_bit_field(element_name, definitions, templates)

    return s


def scala_type_for_member(member_type: str, size: int, definitions: dict[str, DefinedType]) -> str:
    """Get the Scala type for a structure member."""
    if member_type == "int":
        return {1: "Byte", 2: "Short", 4: "Int", 8: "Long"}.get(size, "Int")
    if member_type == "uint":
        # Scala doesn't have unsigned, use next larger signed type
        return {1: "Int", 2: "Int", 4: "Long", 8: "Long"}.get(size, "Long")
    if member_type == "bool":
        return "Boolean" if size == 1 else "Array[Byte]"
    if member_type in ("bytes", "reserved"):
        return "Array[Byte]"
    if member_type == "str":
        return "String"
    # Check if it's a defined type
    if member_type in definitions:
        return member_type
    return member_type


def decode_call_for_member(
    member: dict[str, Any],
    offset: int,
    definitions: dict[str, DefinedType],
) -> str:
    """Generate the decode call for a structure member."""
    member_type = member["type"]
    size = member["size"]
    end = offset + size

    if member_type == "int":
        func = {1: "bytesToInt8LE", 2: "bytesToInt16LE", 4: "bytesToInt32LE", 8: "bytesToInt64LE"}.get(size)
        if func:
            return f"BinaryUtils.{func}(bytes, {offset})"
        return f"bytes.slice({offset}, {end})"
    if member_type == "uint":
        func = {1: "bytesToUint8LE", 2: "bytesToUint16LE", 4: "bytesToUint32LE", 8: "bytesToUint64LE"}.get(size)
        if func:
            return f"BinaryUtils.{func}(bytes, {offset})"
        return f"bytes.slice({offset}, {end})"
    if member_type == "bool":
        if size == 1:
            return f"bytes({offset}) != 0"
        return f"bytes.slice({offset}, {end})"
    if member_type in ("bytes", "reserved"):
        return f"bytes.slice({offset}, {end})"
    if member_type == "str":
        return f'new String(bytes.slice({offset}, {end}).takeWhile(_ != 0), "UTF-8")'
    # Check if it's a defined type
    if member_type in definitions:
        return f"{member_type}.decodeLogEvent(bytes.slice({offset}, {end}))"
    return f"bytes.slice({offset}, {end})"


def encode_call_for_member(
    member: dict[str, Any],
    definitions: dict[str, DefinedType],
) -> str:
    """Generate the encode call for a structure member."""
    member_type = member["type"]
    member_name = member["name"]
    size = member["size"]

    if member_type == "int":
        func = {1: "int8LEtoBytes", 2: "int16LEtoBytes", 4: "int32LEtoBytes", 8: "int64LEtoBytes"}.get(size)
        if func:
            return f"bytes.appendAll(BinaryUtils.{func}(event.{member_name}))"
        return f"bytes.appendAll(event.{member_name})"
    if member_type == "uint":
        func = {1: "uint8LEtoBytes", 2: "uint16LEtoBytes", 4: "uint32LEtoBytes", 8: "uint64LEtoBytes"}.get(size)
        if func:
            return f"bytes.appendAll(BinaryUtils.{func}(event.{member_name}))"
        return f"bytes.appendAll(event.{member_name})"
    if member_type == "bool":
        if size == 1:
            return f"bytes.append(if (event.{member_name}) 1.toByte else 0.toByte)"
        return f"bytes.appendAll(event.{member_name})"
    if member_type in ("bytes", "reserved"):
        return f"bytes.appendAll(event.{member_name})"
    if member_type == "str":
        return f'bytes.appendAll(event.{member_name}.getBytes("UTF-8").take({size}).padTo({size}, 0.toByte))'
    # Check if it's a defined type
    if member_type in definitions:
        return f"bytes.appendAll(event.{member_name}.toByteSeq.get)"
    return f"bytes.appendAll(event.{member_name})"


def render_enum(
    element_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],  # noqa: ARG001
) -> str:
    """Render a Scala enum as a sealed trait with case objects."""
    enumeration = definitions[element_name]
    enum_dict = enumeration.to_dict()

    s = f"""// {enum_dict['display_name']}
// {enum_dict['description']}
sealed trait {element_name} extends ByteSequence {{
  override def SizeInBytes: Int = {enum_dict['size']}
  override def toByteSeq: Try[Seq[Byte]] = Success(Seq({element_name}.toByte(this)))
  def toDisplayString: String = {element_name}.toDisplayString(this)
}}

object {element_name} {{
  // Wrapper for unknown enum values
  final case class UnknownValue(value: Byte) extends {element_name}
"""
    # Generate case objects (escape Scala keywords)
    for value in enum_dict.get("values", []):
        escaped_label = escape_scala_keyword(value['label'])
        s += f"  case object {escaped_label} extends {element_name}\n"

    # Generate fromByte
    s += f"  def fromByte(value: Byte): Option[{element_name}] = value match {{\n"
    for value in enum_dict.get("values", []):
        escaped_label = escape_scala_keyword(value['label'])
        s += f"case {value['value']} => Some({element_name}.{escaped_label})\n"
    s += "    case _ => None\n"
    s += "  }\n\n"

    # Generate toByte
    s += f"  def toByte(value: {element_name}): Byte = value match {{\n"
    for value in enum_dict.get("values", []):
        escaped_label = escape_scala_keyword(value['label'])
        s += f"case {element_name}.{escaped_label} => {value['value']}.toByte\n"
    s += "    case UnknownValue(v) => v\n"
    s += "  }\n\n"

    # Generate toDisplayString
    s += f"  def toDisplayString(value: {element_name}): String = value match {{\n"
    for value in enum_dict.get("values", []):
        escaped_label = escape_scala_keyword(value['label'])
        s += f'case {element_name}.{escaped_label} => "{value["label"]}"\n'
    s += f'    case UnknownValue(v) => f"${{v & 0xFF}}%02X (len={enum_dict["size"]})"\n'
    s += "  }\n\n"

    # Generate fromDisplayString
    s += f"  def fromDisplayString(s: String): Option[{element_name}] = {{\n"
    for value in enum_dict.get("values", []):
        escaped_label = escape_scala_keyword(value['label'])
        s += f'    if (s == "{value["label"]}") return Some({element_name}.{escaped_label})\n'
    s += "    None\n"
    s += "  }\n\n"

    # Generate decodeLogEvent
    s += f"  def decodeLogEvent(bytes: Array[Byte]): {element_name} =\n"
    s += "    fromByte(bytes(0)).getOrElse(UnknownValue(bytes(0)))\n"
    s += "}\n\n"

    return s


def render_structure(
    structure_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],  # noqa: ARG001
    extends_trait: str | None = None,
) -> str:
    """Render a Scala structure as a case class with codec."""
    structure = definitions[structure_name].as_structure()
    structure_dict = structure.to_dict()

    # Render any member types first
    s = ""
    for member in structure.members:
        if member.type in definitions and member.type not in rendered:
            s += render_definition(member.type, definitions, templates)

    # Build case class
    base_trait = extends_trait if extends_trait else "ByteSequence"
    s += f"// {structure_dict['display_name']}\n"
    s += f"// {structure_dict['description']}\n"
    s += f"final case class {structure_name}(\n"

    # Generate fields
    member_lines = []
    for member in structure_dict.get("members", []):
        if member["type"] == "reserved":
            member_lines.append(f"  {member['name']}: Array[Byte],")
        else:
            scala_type = scala_type_for_member(member["type"], member["size"], definitions)
            comment = f" // {member['description']}" if member.get("description") else ""
            member_lines.append(f"  {member['name']}: {scala_type},{comment}")

    s += "\n".join(member_lines)
    s += f"\n) extends {base_trait} with CustomJsonSerializer {{\n"
    s += f"  override def SizeInBytes: Int = {structure_name}.SizeInBytes\n"
    s += f"  override def toByteSeq: Try[Seq[Byte]] = {structure_name}.encode(this)\n"
    s += "\n"
    s += "  // JSON serialization - uses json4s automatic case class serialization\n"
    s += f"  type ObjectToSerialize = {structure_name}\n"
    s += f"  protected def getObjectToSerialize(): {structure_name} = this\n"
    s += "}\n\n"

    # Generate companion object
    s += f"object {structure_name} extends ByteSequenceCodec[{structure_name}] {{\n\n"
    s += f"  final val SizeInBytes = {structure_dict['size']}\n\n"
    s += "  // Binary decode/encode\n"
    s += f"  override def decode(bytes: Array[Byte], streamPositionHead: Long): Try[{structure_name}] = Try {{\n"
    s += "    decodeLogEvent(bytes)\n"
    s += "  }\n\n"
    s += f"  override def encode(event: {structure_name}): Try[Seq[Byte]] = Try {{\n"
    s += "    encodeLogEvent(event)\n"
    s += "  }\n\n"

    # Generate decodeLogEvent
    s += f"  def decodeLogEvent(bytes: Array[Byte]): {structure_name} = {{\n"
    s += f"    {structure_name}(\n"
    offset = 0
    for member in structure_dict.get("members", []):
        decode_expr = decode_call_for_member(member, offset, definitions)
        s += f"      {member['name']} = {decode_expr},\n"
        offset += member["size"]
    s += "    )\n"
    s += "  }\n\n"

    # Generate encodeLogEvent
    s += f"  def encodeLogEvent(event: {structure_name}): Seq[Byte] = {{\n"
    s += "    val bytes = mutable.ArrayBuffer.empty[Byte]\n"
    for member in structure_dict.get("members", []):
        encode_expr = encode_call_for_member(member, definitions)
        s += f"    {encode_expr}\n"
    s += "    bytes.toSeq\n"
    s += "  }\n"
    s += "}\n\n"

    return s


def render_group(
    group_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
) -> str:
    """Render a Scala group as a sealed trait with decode dispatcher."""
    group = definitions[group_name].as_group()

    if not group.members:
        return ""

    s = f"// {group.display_name}\n"
    s += f"// {group.description}\n"
    s += f"sealed trait {group_name} extends ByteSequence\n\n"

    # Generate decode object
    s += f"object {group_name} {{\n"
    s += f"  def decode(bytes: Array[Byte], streamPositionHead: Long): Try[{group_name}] = {{\n"
    s += f'    if (bytes.length < {group.size}) return Failure(new Exception("Insufficient bytes for tag"))\n'

    # Determine tag read based on size
    if group.size == 1:
        s += "    val tag = bytes(0) & 0xFF\n"
    elif group.size == 2:
        s += "    val tag = BinaryUtils.bytesToUint16LE(bytes, 0)\n"
    elif group.size == 4:
        s += "    val tag = BinaryUtils.bytesToUint32LE(bytes, 0).toInt\n"
    else:
        s += f"    val tag = bytes({group.size - 1}) & 0xFF\n"

    s += f"    val structureBytes = bytes.drop({group.size})  // Skip tag bytes before passing to structure decoder\n"
    s += "    tag match {\n"

    # Generate match cases (use L suffix for large values)
    for member in sorted(group.members, key=lambda m: m.value):
        tag_value = format_large_int(member.value)
        s += f"case {tag_value} => {member.type}.decode(structureBytes, streamPositionHead).asInstanceOf[Try[{group_name}]]\n"

    s += '      case _ => Failure(new Exception(s"Unknown tag: $tag"))\n'
    s += "    }\n"
    s += "  }\n\n"

    s += f"  def decodeLogEvent(bytes: Array[Byte]): {group_name} =\n"
    s += "    decode(bytes, 0L).get\n"
    s += "}\n\n"

    # Render member structures with extends trait
    for member in group.members:
        if member.type not in rendered:
            s += render_structure_with_group(member.type, definitions, templates, group_name)

    return s


def render_structure_with_group(
    structure_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
    group_name: str,
) -> str:
    """Render a structure that extends a group trait."""
    if structure_name in rendered:
        return ""
    rendered.add(structure_name)

    structure = definitions[structure_name].as_structure()
    structure_dict = structure.to_dict()

    # Render any member types first
    s = ""
    for member in structure.members:
        if member.type in definitions and member.type not in rendered:
            s += render_definition(member.type, definitions, templates)

    # Build case class extending the group trait
    s += f"// {structure_dict['display_name']}\n"
    s += f"// {structure_dict['description']}\n"
    s += f"final case class {structure_name}(\n"

    # Generate fields
    member_lines = []
    for member in structure_dict.get("members", []):
        if member["type"] == "reserved":
            member_lines.append(f"  {member['name']}: Array[Byte],")
        else:
            scala_type = scala_type_for_member(member["type"], member["size"], definitions)
            comment = f" // {member['description']}" if member.get("description") else ""
            member_lines.append(f"  {member['name']}: {scala_type},{comment}")

    s += "\n".join(member_lines)
    s += f"\n) extends {group_name} with CustomJsonSerializer {{\n"
    s += f"  override def SizeInBytes: Int = {structure_name}.SizeInBytes\n"
    s += f"  override def toByteSeq: Try[Seq[Byte]] = {structure_name}.encode(this)\n"
    s += "\n"
    s += "  // JSON serialization - uses json4s automatic case class serialization\n"
    s += f"  type ObjectToSerialize = {structure_name}\n"
    s += f"  protected def getObjectToSerialize(): {structure_name} = this\n"
    s += "}\n\n"

    # Generate companion object
    s += f"object {structure_name} extends ByteSequenceCodec[{structure_name}] {{\n\n"
    s += f"  final val SizeInBytes = {structure_dict['size']}\n\n"
    s += "  // Binary decode/encode\n"
    s += f"  override def decode(bytes: Array[Byte], streamPositionHead: Long): Try[{structure_name}] = Try {{\n"
    s += "    decodeLogEvent(bytes)\n"
    s += "  }\n\n"
    s += f"  override def encode(event: {structure_name}): Try[Seq[Byte]] = Try {{\n"
    s += "    encodeLogEvent(event)\n"
    s += "  }\n\n"

    # Generate decodeLogEvent
    s += f"  def decodeLogEvent(bytes: Array[Byte]): {structure_name} = {{\n"
    s += f"    {structure_name}(\n"
    offset = 0
    for member in structure_dict.get("members", []):
        decode_expr = decode_call_for_member(member, offset, definitions)
        s += f"      {member['name']} = {decode_expr},\n"
        offset += member["size"]
    s += "    )\n"
    s += "  }\n\n"

    # Generate encodeLogEvent
    s += f"  def encodeLogEvent(event: {structure_name}): Seq[Byte] = {{\n"
    s += "    val bytes = mutable.ArrayBuffer.empty[Byte]\n"
    for member in structure_dict.get("members", []):
        encode_expr = encode_call_for_member(member, definitions)
        s += f"    {encode_expr}\n"
    s += "    bytes.toSeq\n"
    s += "  }\n"
    s += "}\n\n"

    return s


def render_bit_field(
    bit_field_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
) -> str:
    """Render a Scala bit field as a case class with bit manipulation."""
    bit_field = definitions[bit_field_name].as_bit_field()
    bit_field_dict = bit_field.to_dict()

    # Render any member types first
    s = ""
    for member in bit_field.members:
        if member.type in definitions and member.type not in rendered:
            s += render_definition(member.type, definitions, templates)

    # Determine the underlying type for bit operations
    bits = bit_field_dict["size"] * 8
    raw_type = f"u{bits}" if bits <= 32 else "Long"
    read_func = {8: "bytesToUint8LE", 16: "bytesToUint16LE", 32: "bytesToUint32LE", 64: "bytesToUint64LE"}.get(bits, "bytesToUint32LE")
    write_func = {8: "uint8LEtoBytes", 16: "uint16LEtoBytes", 32: "uint32LEtoBytes", 64: "uint64LEtoBytes"}.get(bits, "uint32LEtoBytes")

    # Build case class
    s += f"// {bit_field_dict['display_name']}\n"
    s += f"// {bit_field_dict['description']}\n"
    s += f"final case class {bit_field_name}(\n"

    # Generate fields (excluding reserved)
    member_lines = []
    for member in bit_field_dict.get("members", []):
        if member["type"] == "reserved":
            s += f"  // Reserved: bits {member['start']}-${{member.last}}\n"
        else:
            scala_type = "Int"  # Bit fields are typically small enough for Int
            if member["type"] == "bool":
                scala_type = "Boolean" if member["bits"] == 1 else "Int"
            member_lines.append(f"  {member['name']}: {scala_type},")

    s += "\n".join(member_lines)
    s += f"\n) extends ByteSequence with CustomJsonSerializer {{\n"
    s += f"  override def SizeInBytes: Int = {bit_field_name}.SizeInBytes\n"
    s += f"  override def toByteSeq: Try[Seq[Byte]] = {bit_field_name}.encode(this)\n"
    s += "\n"
    s += "  // JSON serialization - uses json4s automatic case class serialization\n"
    s += f"  type ObjectToSerialize = {bit_field_name}\n"
    s += f"  protected def getObjectToSerialize(): {bit_field_name} = this\n"
    s += "}\n\n"

    # Generate companion object
    s += f"object {bit_field_name} extends ByteSequenceCodec[{bit_field_name}] {{\n"
    s += f"  final val SizeInBytes = {bit_field_dict['size']}\n\n"

    s += f"  override def decode(bytes: Array[Byte], streamPositionHead: Long): Try[{bit_field_name}] = Try {{\n"
    s += "    decodeLogEvent(bytes)\n"
    s += "  }\n\n"

    s += f"  override def encode(event: {bit_field_name}): Try[Seq[Byte]] = Try {{\n"
    s += "    encodeLogEvent(event)\n"
    s += "  }\n\n"

    # Generate decodeLogEvent
    s += f"  def decodeLogEvent(bytes: Array[Byte]): {bit_field_name} = {{\n"
    s += f"    val rawBits = BinaryUtils.{read_func}(bytes, 0)\n"
    s += f"    {bit_field_name}(\n"

    for member in bit_field_dict.get("members", []):
        if member["type"] == "reserved":
            continue
        mask = (1 << member["bits"]) - 1
        mask_str = format_large_int(mask)
        shift = member["start"]
        if member["type"] == "bool" and member["bits"] == 1:
            s += f"      {member['name']} = ((rawBits >> {shift}) & {mask_str}) != 0,\n"
        else:
            s += f"      {member['name']} = ((rawBits >> {shift}) & {mask_str}).toInt,\n"

    s += "    )\n"
    s += "  }\n\n"

    # Generate encodeLogEvent
    scala_raw_type = {8: "Int", 16: "Int", 32: "Int", 64: "Long"}.get(bits, "Int")
    s += f"  def encodeLogEvent(value: {bit_field_name}): Seq[Byte] = {{\n"
    s += f"    var rawBits: {scala_raw_type} = 0\n"

    for member in bit_field_dict.get("members", []):
        if member["type"] == "reserved":
            continue
        mask = (1 << member["bits"]) - 1
        mask_str = format_large_int(mask)
        shift = member["start"]
        if member["type"] == "bool" and member["bits"] == 1:
            s += f"    rawBits |= ((if (value.{member['name']}) 1 else 0) << {shift})\n"
        else:
            s += f"    rawBits |= ((value.{member['name']} & {mask_str}) << {shift})\n"

    if bits == 64:
        s += f"    BinaryUtils.{write_func}(rawBits).toSeq\n"
    else:
        s += f"    BinaryUtils.{write_func}(rawBits.toLong).toSeq\n"
    s += "  }\n"
    s += "}\n\n"

    return s
