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

# Constants for Scala integer limits
INT_MAX_VALUE = 2147483647
INT_MIN_VALUE = -2147483648

# Constants for path parsing
SRC_MAIN_SCALA_PATH = ("src", "main", "scala")
SRC_MAIN_SCALA_LEN = 3

# Constants for byte sizes
BITS_8 = 8
BITS_16 = 16
BITS_32 = 32
BITS_64 = 64
BYTES_1 = 1
BYTES_2 = 2
BYTES_4 = 4
BYTES_8 = 8

# Scala reserved keywords that need backtick escaping
SCALA_KEYWORDS = {
    "abstract",
    "case",
    "catch",
    "class",
    "def",
    "do",
    "else",
    "extends",
    "false",
    "final",
    "finally",
    "for",
    "forSome",
    "if",
    "implicit",
    "import",
    "lazy",
    "match",
    "new",
    "null",
    "object",
    "override",
    "package",
    "private",
    "protected",
    "return",
    "sealed",
    "super",
    "this",
    "throw",
    "trait",
    "true",
    "try",
    "type",
    "val",
    "var",
    "while",
    "with",
    "yield",
}


def escape_scala_keyword(name: str) -> str:
    """Escape Scala keywords with backticks."""
    return f"`{name}`" if name in SCALA_KEYWORDS else name


def format_large_int(value: int) -> str:
    """Format integer literal, adding L suffix for values > Int.MaxValue."""
    if value > INT_MAX_VALUE or value < INT_MIN_VALUE:
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
    """Extract Scala package from file path (e.g., com.example.generated)."""
    parts = output_file.parts
    try:
        # Look for scala/src/main/scala pattern
        if "scala" in parts:
            scala_idx = parts.index("scala")
            # Check for src/main/scala pattern after scala
            remaining = parts[scala_idx + 1 :]
            if (
                len(remaining) >= SRC_MAIN_SCALA_LEN
                and remaining[:SRC_MAIN_SCALA_LEN] == SRC_MAIN_SCALA_PATH
            ):
                package_parts = remaining[
                    SRC_MAIN_SCALA_LEN:-1
                ]  # Exclude the filename
                return ".".join(package_parts)
        # Look for just src/main/scala pattern
        if "src" in parts:
            src_idx = parts.index("src")
            remaining = parts[src_idx:]
            if (
                len(remaining) >= SRC_MAIN_SCALA_LEN
                and remaining[:SRC_MAIN_SCALA_LEN] == SRC_MAIN_SCALA_PATH
            ):
                package_parts = remaining[
                    SRC_MAIN_SCALA_LEN:-1
                ]  # Exclude the filename
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


def scala_type_for_member(
    member_type: str,
    size: int,
    definitions: dict[str, DefinedType],  # noqa: ARG001
) -> str:
    """Get the Scala type for a structure member."""
    # Type mappings for primitive types
    int_types = {
        BYTES_1: "Byte",
        BYTES_2: "Short",
        BYTES_4: "Int",
        BYTES_8: "Long",
    }
    uint_types = {
        BYTES_1: "Int",
        BYTES_2: "Int",
        BYTES_4: "Long",
        BYTES_8: "Long",
    }
    type_map = {
        "int": int_types.get(size, "Int"),
        "uint": uint_types.get(size, "Long"),
        "bool": "Boolean" if size == BYTES_1 else "Array[Byte]",
        "bytes": "Array[Byte]",
        "reserved": "Array[Byte]",
        "str": "String",
    }
    if member_type in type_map:
        return type_map[member_type]
    # Check if it's a defined type or use as-is
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

    int_funcs = {
        BYTES_1: "bytesToInt8LE",
        BYTES_2: "bytesToInt16LE",
        BYTES_4: "bytesToInt32LE",
        BYTES_8: "bytesToInt64LE",
    }
    uint_funcs = {
        BYTES_1: "bytesToUint8LE",
        BYTES_2: "bytesToUint16LE",
        BYTES_4: "bytesToUint32LE",
        BYTES_8: "bytesToUint64LE",
    }

    if member_type == "int" and size in int_funcs:
        return f"BinaryUtils.{int_funcs[size]}(bytes, {offset})"
    if member_type == "uint" and size in uint_funcs:
        return f"BinaryUtils.{uint_funcs[size]}(bytes, {offset})"
    if member_type == "bool" and size == BYTES_1:
        return f"bytes({offset}) != 0"
    if member_type == "str":
        return f'new String(bytes.slice({offset}, {end}).takeWhile(_ != 0), "UTF-8")'
    if member_type in definitions:
        return f"{member_type}.fromBytes(bytes.slice({offset}, {end}))"
    return f"bytes.slice({offset}, {end})"


def _json_type_for_primitive(member_type: str, size: int) -> str | None:
    """Get JSON type for primitive member types."""
    if member_type == "int":
        int_types = {
            BYTES_1: "Byte",
            BYTES_2: "Short",
            BYTES_4: "Int",
            BYTES_8: "Long",
        }
        return int_types.get(size, "Int")
    if member_type == "uint":
        return "Int" if size == BYTES_1 else "String"  # Hex string for > 1 byte
    primitive_map = {
        "bool": "Boolean",
        "bytes": "Array[Byte]",
        "reserved": "String",  # Hex string for round-trip
        "str": "String",
    }
    return primitive_map.get(member_type)


def json_type_for_member(
    member: dict[str, Any],
    definitions: dict[str, DefinedType],
) -> str:
    """Get the JSON intermediate type for a structure member (for deserialization)."""
    member_type = member["type"]
    size = member["size"]

    # Check primitive types first
    primitive_result = _json_type_for_primitive(member_type, size)
    if primitive_result is not None:
        return primitive_result

    # Check defined types (enum or nested structure)
    if member_type in definitions:
        defn = definitions[member_type]
        return "String" if isinstance(defn, Enumeration) else "JValue"

    return "JValue"  # Fallback


def _scala_to_json_for_uint(member_name: str, size: int) -> str:
    """Get Scala to JSON conversion for unsigned int."""
    if size == BYTES_1:
        return member_name
    hex_formats = {BYTES_2: "%04X", BYTES_4: "%08X", BYTES_8: "%016X"}
    fmt = hex_formats.get(size, "%016X")
    return f'f"0x${{{member_name}}}{fmt}"'


def _scala_to_json_for_defined_type(
    member_name: str, member_type: str, definitions: dict[str, DefinedType]
) -> str:
    """Get Scala to JSON conversion for defined types."""
    defn = definitions[member_type]
    if isinstance(defn, Enumeration):
        return f"{member_name}.toDisplayString"
    if isinstance(defn, (Structure, BitField)):
        return f"{member_name}.serializeToJValue()"
    if isinstance(defn, Group):
        return f"parse({member_name}.asInstanceOf[CustomJsonSerializer].serialize())"
    return (
        f"{member_name}.asInstanceOf[CustomJsonSerializer].serializeToJValue()"
    )


def scala_to_json_conversion(
    member: dict[str, Any],
    definitions: dict[str, DefinedType],
) -> str:
    """Generate the conversion from Scala type to JSON-friendly type."""
    member_type = member["type"]
    member_name = member["name"]
    size = member["size"]

    # Direct passthrough types
    if member_type in ("int", "bool", "bytes", "str"):
        return member_name

    # Unsigned int with hex formatting
    if member_type == "uint":
        return _scala_to_json_for_uint(member_name, size)

    # Reserved fields as hex string
    if member_type == "reserved":
        return member_name + '.map(b => f"${b & 0xFF}%02X").mkString'

    # Defined types (enum, structure, group, bitfield)
    if member_type in definitions:
        return _scala_to_json_for_defined_type(
            member_name, member_type, definitions
        )

    return member_name


def _json_to_scala_for_defined_type(
    member_name: str, member_type: str, definitions: dict[str, DefinedType]
) -> str:
    """Get JSON to Scala conversion for defined types."""
    defn = definitions[member_type]
    if isinstance(defn, Enumeration):
        return (
            f"{member_type}.fromDisplayString(j.{member_name})"
            f".getOrElse({member_type}.UnknownValue(0))"
        )
    if isinstance(defn, Group):
        return f"{member_type}.decodeFromJson(compact(render(j.{member_name})))"
    return f"{member_type}.deserialize(compact(render(j.{member_name})))"


def json_to_scala_conversion(
    member: dict[str, Any],
    definitions: dict[str, DefinedType],
) -> str:
    """Generate the conversion from JSON value to Scala type."""
    member_type = member["type"]
    member_name = member["name"]
    size = member["size"]

    # Direct passthrough types
    if member_type in ("int", "bool", "bytes", "str"):
        return f"j.{member_name}"

    # Reserved fields from hex string
    if member_type == "reserved":
        return f"j.{member_name}.grouped(2).map(s => Integer.parseInt(s, 16).toByte).toArray"

    # Unsigned integers need hex parsing for sizes > 1 byte
    if member_type == "uint":
        if size == BYTES_1:
            return f"j.{member_name}"
        suffix = ".toInt" if size == BYTES_2 else ""
        return f"BinaryUtils.parseHexString(j.{member_name}){suffix}"

    # Defined types (enums, structures, groups)
    if member_type in definitions:
        return _json_to_scala_for_defined_type(
            member_name, member_type, definitions
        )

    return f"j.{member_name}"


def encode_call_for_member(
    member: dict[str, Any],
    definitions: dict[str, DefinedType],
) -> str:
    """Generate the encode call for a structure member."""
    member_type = member["type"]
    member_name = member["name"]
    size = member["size"]

    int_funcs = {
        BYTES_1: "int8LEtoBytes",
        BYTES_2: "int16LEtoBytes",
        BYTES_4: "int32LEtoBytes",
        BYTES_8: "int64LEtoBytes",
    }
    uint_funcs = {
        BYTES_1: "uint8LEtoBytes",
        BYTES_2: "uint16LEtoBytes",
        BYTES_4: "uint32LEtoBytes",
        BYTES_8: "uint64LEtoBytes",
    }

    if member_type == "int" and size in int_funcs:
        return f"bytes.appendAll(BinaryUtils.{int_funcs[size]}(event.{member_name}))"
    if member_type == "uint" and size in uint_funcs:
        return f"bytes.appendAll(BinaryUtils.{uint_funcs[size]}(event.{member_name}))"
    if member_type == "bool" and size == BYTES_1:
        return f"bytes.append(if (event.{member_name}) 1.toByte else 0.toByte)"
    if member_type == "str":
        return f'bytes.appendAll(event.{member_name}.getBytes("UTF-8").take({size}).padTo({size}, 0.toByte))'
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

    s = f"""// {enum_dict["display_name"]}
// {enum_dict["description"]}
sealed trait {element_name} extends ByteSequence {{
  override def SizeInBytes: Int = {enum_dict["size"]}
  override def toByteSeq: Try[Seq[Byte]] = Success(Seq({element_name}.toByte(this)))
  def toDisplayString: String = {element_name}.toDisplayString(this)
}}

object {element_name} {{
  // Wrapper for unknown enum values
  final case class UnknownValue(value: Byte) extends {element_name}
"""
    # Generate case objects (escape Scala keywords)
    for value in enum_dict.get("values", []):
        escaped_label = escape_scala_keyword(value["label"])
        s += f"  case object {escaped_label} extends {element_name}\n"

    # Generate fromByte
    s += f"  def fromByte(value: Byte): Option[{element_name}] = value match {{\n"
    for value in enum_dict.get("values", []):
        escaped_label = escape_scala_keyword(value["label"])
        s += f"case {value['value']} => Some({element_name}.{escaped_label})\n"
    s += "    case _ => None\n"
    s += "  }\n\n"

    # Generate toByte
    s += f"  def toByte(value: {element_name}): Byte = value match {{\n"
    for value in enum_dict.get("values", []):
        escaped_label = escape_scala_keyword(value["label"])
        s += f"case {element_name}.{escaped_label} => {value['value']}.toByte\n"
    s += "    case UnknownValue(v) => v\n"
    s += "  }\n\n"

    # Generate toDisplayString
    s += f"  def toDisplayString(value: {element_name}): String = value match {{\n"
    for value in enum_dict.get("values", []):
        escaped_label = escape_scala_keyword(value["label"])
        s += f'case {element_name}.{escaped_label} => "{value["label"]}"\n'
    s += f'    case UnknownValue(v) => f"${{v & 0xFF}}%02X (len={enum_dict["size"]})"\n'
    s += "  }\n\n"

    # Generate fromDisplayString
    s += f"  def fromDisplayString(s: String): Option[{element_name}] = {{\n"
    for value in enum_dict.get("values", []):
        escaped_label = escape_scala_keyword(value["label"])
        s += f'    if (s == "{value["label"]}") return Some({element_name}.{escaped_label})\n'
    s += (
        '    // Parse UnknownValue format like "31 (len=1)" or "0x31 (len=1)"\n'
    )
    s += '    val hexPrefixedPattern = """^0x([0-9A-Fa-f]+) \\(len=\\d+\\)$""".r\n'
    s += (
        '    val hexNoPrefixPattern = """^([0-9A-Fa-f]+) \\(len=\\d+\\)$""".r\n'
    )
    s += "    s match {\n"
    s += "      case hexPrefixedPattern(hexValue) => Some(UnknownValue(Integer.parseInt(hexValue, 16).toByte))\n"
    s += "      case hexNoPrefixPattern(hexValue) =>\n"
    s += "        try { Some(UnknownValue(Integer.parseInt(hexValue, 16).toByte)) }\n"
    s += "        catch { case _: NumberFormatException => None }\n"
    s += "      case _ => None\n"
    s += "    }\n"
    s += "  }\n\n"

    # Generate fromBytes
    s += f"  def fromBytes(bytes: Array[Byte]): {element_name} =\n"
    s += "    fromByte(bytes(0)).getOrElse(UnknownValue(bytes(0)))\n"
    s += "}\n\n"

    return s


def _render_structure_fields(
    members: list[dict[str, Any]], definitions: dict[str, DefinedType]
) -> tuple[list[str], list[dict[str, Any]]]:
    """Generate field lines for case class and collect all members for JSON."""
    member_lines = []
    all_members = []
    for member in members:
        if member["type"] == "reserved":
            member_lines.append(f"  {member['name']}: Array[Byte],")
        else:
            scala_type = scala_type_for_member(
                member["type"], member["size"], definitions
            )
            comment = (
                f" // {member['description']}"
                if member.get("description")
                else ""
            )
            member_lines.append(f"  {member['name']}: {scala_type},{comment}")
        all_members.append(member)
    return member_lines, all_members


def _render_json_intermediate_class(
    structure_name: str,
    all_members: list[dict[str, Any]],
    definitions: dict[str, DefinedType],
) -> str:
    """Render JSON intermediate case class for serialization/deserialization."""
    s = f"// JSON intermediate class for {structure_name} serialization/deserialization\n"
    s += f"case class {structure_name}Json(\n"
    s += "  _type: String,\n"
    json_field_lines = [
        f"  {m['name']}: {json_type_for_member(m, definitions)}"
        for m in all_members
    ]
    s += ",\n".join(json_field_lines)
    s += "\n)\n\n"
    return s


def _render_structure_companion(
    structure_name: str,
    structure_dict: dict[str, Any],
    members: list[dict[str, Any]],
    definitions: dict[str, DefinedType],
) -> str:
    """Render companion object with codec and JSON deserializer."""
    s = f"object {structure_name} extends ByteSequenceCodec[{structure_name}] with CustomJsonDeserializer[{structure_name}] {{\n\n"
    s += f"  final val SizeInBytes = {structure_dict['size']}\n\n"
    s += "  // Binary decode/encode\n"
    s += f"  override def decode(bytes: Array[Byte], streamPositionHead: Long): Try[{structure_name}] = Try {{\n"
    s += "    fromBytes(bytes)\n"
    s += "  }\n\n"
    s += f"  override def encode(event: {structure_name}): Try[Seq[Byte]] = Try {{\n"
    s += "    toBytes(event)\n  }\n\n"

    # fromBytes
    s += f"  def fromBytes(bytes: Array[Byte]): {structure_name} = {{\n"
    s += f"    {structure_name}(\n"
    offset = 0
    for member in members:
        decode_expr = decode_call_for_member(member, offset, definitions)
        s += f"      {member['name']} = {decode_expr},\n"
        offset += member["size"]
    s += "    )\n  }\n\n"

    # toBytes
    s += f"  def toBytes(event: {structure_name}): Seq[Byte] = {{\n"
    s += "    val bytes = mutable.ArrayBuffer.empty[Byte]\n"
    for member in members:
        s += f"    {encode_call_for_member(member, definitions)}\n"
    s += "    bytes.toSeq\n  }\n\n"

    # fromJson
    s += "  // JSON deserialization\n"
    s += f"  override protected def fromJson(json: String)(implicit formats: Formats): {structure_name} = {{\n"
    s += f"    val j = Serialization.read[{structure_name}Json](json)\n"
    s += f"    {structure_name}(\n"
    for member in members:
        s += f"      {member['name']} = {json_to_scala_conversion(member, definitions)},\n"
    s += "    )\n  }\n"
    s += "}\n\n"
    return s


def render_structure(
    structure_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
    extends_trait: str | None = None,
) -> str:
    """Render a Scala structure as a case class with codec and JSON round-trip."""
    structure = definitions[structure_name].as_structure()
    structure_dict = structure.to_dict()
    members = structure_dict.get("members", [])

    # Render any member types first
    s = ""
    for member in structure.members:
        if member.type in definitions and member.type not in rendered:
            s += render_definition(member.type, definitions, templates)

    # Build case class
    base_trait = extends_trait if extends_trait else "ByteSequence"
    s += f"// {structure_dict['display_name']}\n// {structure_dict['description']}\n"
    s += f"final case class {structure_name}(\n"

    member_lines, all_members = _render_structure_fields(members, definitions)
    s += "\n".join(member_lines)
    s += f"\n) extends {base_trait} with CustomJsonSerializer {{\n"
    s += f"  override def SizeInBytes: Int = {structure_name}.SizeInBytes\n"
    s += f"  override def toByteSeq: Try[Seq[Byte]] = {structure_name}.encode(this)\n\n"
    s += "  // JSON serialization - convert to JSON-friendly intermediate form with type discriminator\n"
    s += f"  type ObjectToSerialize = {structure_name}Json\n"
    s += f"  protected def getObjectToSerialize(): {structure_name}Json = {structure_name}Json(\n"
    s += f'    _type = "{structure_name}",\n'
    for member in all_members:
        s += f"    {member['name']} = {scala_to_json_conversion(member, definitions)},\n"
    s += "  )\n}\n\n"

    s += _render_json_intermediate_class(
        structure_name, all_members, definitions
    )
    s += _render_structure_companion(
        structure_name, structure_dict, members, definitions
    )
    return s


def _get_structure_fields(
    type_name: str,
    definitions: dict[str, DefinedType],
) -> dict[str, tuple[str, int]] | None:
    """Get fields from a structure as {name: (type, size)} dict, or None if invalid."""
    if type_name not in definitions:
        return None
    structure = definitions[type_name]
    if not hasattr(structure, "members"):
        return None
    return {m.name: (m.type, m.size) for m in structure.members}


def find_common_fields(
    group: Group,
    definitions: dict[str, DefinedType],
) -> list[tuple[str, str, int]]:
    """Find fields that are common to all members of a group.

    Returns a list of (field_name, field_type, field_size) tuples for fields that:
    1. Exist in ALL member structures
    2. Have the same type AND size in all members

    This allows generating abstract methods in the sealed trait.
    """
    if not group.members:
        return []

    # Get the first member's fields as the baseline
    candidate_fields = _get_structure_fields(group.members[0].type, definitions)
    if candidate_fields is None:
        return []

    # Check all other members - keep only fields that exist with same type AND size
    for group_member in group.members[1:]:
        member_fields = _get_structure_fields(group_member.type, definitions)
        if member_fields is None:
            return []

        # Keep only fields that match in both name and (type, size)
        candidate_fields = {
            name: type_size
            for name, type_size in candidate_fields.items()
            if member_fields.get(name) == type_size
        }

    # Return as list of tuples (name, type, size), sorted by field name
    return sorted(
        [
            (name, type_, size)
            for name, (type_, size) in candidate_fields.items()
        ]
    )


def _get_default_value_for_type(scala_type: str) -> str:
    """Return a default value expression for a Scala type."""
    defaults = {
        "Array[Byte]": "Array.empty[Byte]",
        "Int": "0",
        "Short": "0",
        "Byte": "0",
        "Long": "0L",
        "Boolean": "false",
        "String": '""',
    }
    return defaults.get(scala_type, f"null.asInstanceOf[{scala_type}]")


def _render_group_trait(
    group_name: str,
    common_fields: list[tuple[str, str, int]],
    definitions: dict[str, DefinedType],
) -> str:
    """Render the sealed trait declaration for a group."""
    if not common_fields:
        return f"sealed trait {group_name} extends ByteSequence\n\n"

    lines = [f"sealed trait {group_name} extends ByteSequence {{"]
    for field_name, field_type, field_size in common_fields:
        scala_type = scala_type_for_member(field_type, field_size, definitions)
        if field_type in definitions:
            scala_type = field_type
        lines.append(f"  def {field_name}: {scala_type}")
    lines.append("}\n")
    return "\n".join(lines) + "\n"


def _render_raw_data_class(
    group_name: str,
    group_size: int,
    common_fields: list[tuple[str, str, int]],
    definitions: dict[str, DefinedType],
) -> str:
    """Render the RawData fallback case class for unrecognized tags."""
    s = f"/** Fallback for unrecognized tags in {group_name} group - preserves raw bytes */\n"
    s += f"final case class {group_name}_RawData(\n"
    s += "  tag: Int,\n"
    s += "  rawBytes: Array[Byte]\n"
    s += f") extends {group_name} with CustomJsonSerializer {{\n"
    s += f"  override def SizeInBytes: Int = rawBytes.length + {group_size}\n"
    s += (
        "  override def toByteSeq: Try[Seq[Byte]] = Success(rawBytes.toSeq)\n\n"
    )
    s += f"  type ObjectToSerialize = {group_name}_RawDataJson\n"
    s += f"  protected def getObjectToSerialize(): {group_name}_RawDataJson = "
    s += (
        f'{group_name}_RawDataJson("{group_name}_RawData", tag, rawBytes'
        '.map(b => f"${b & 0xFF}%02X").mkString)\n'
    )

    for field_name, field_type, field_size in common_fields:
        scala_type = scala_type_for_member(field_type, field_size, definitions)
        if field_type in definitions:
            scala_type = field_type
        default = _get_default_value_for_type(scala_type)
        s += f"  override def {field_name}: {scala_type} = {default}\n"

    s += "}\n\n"

    # JSON helper class with _type discriminator
    s += f"case class {group_name}_RawDataJson(\n"
    s += "  _type: String,\n"
    s += "  tag: Int,\n"
    s += "  rawBytes: String\n"  # Changed to String for hex representation
    s += ") {\n"
    s += f'  val groupType: String = "{group_name}"\n'
    s += '  val tagHex: String = f"0x${tag}%02X"\n'
    s += "}\n\n"
    return s


def _render_group_decoder(group_name: str, group: Group) -> str:
    """Render the decode object for a group."""
    tag_readers = {
        BYTES_1: "    val tag = bytes(0) & 0xFF\n",
        BYTES_2: "    val tag = BinaryUtils.bytesToUint16LE(bytes, 0)\n",
        BYTES_4: "    val tag = BinaryUtils.bytesToUint32LE(bytes, 0).toInt\n",
    }

    s = f"object {group_name} {{\n"
    s += "  implicit val formats: Formats = DefaultFormats\n\n"
    s += f"  def decode(bytes: Array[Byte], streamPositionHead: Long): Try[{group_name}] = {{\n"
    s += f'    if (bytes.length < {group.size}) return Failure(new Exception("Insufficient bytes for tag"))\n'
    s += tag_readers.get(
        group.size, f"    val tag = bytes({group.size - 1}) & 0xFF\n"
    )
    s += f"    val structureBytes = bytes.drop({group.size})\n"
    s += "    tag match {\n"

    for member in sorted(group.members, key=lambda m: m.value):
        tag_value = format_large_int(member.value)
        s += f"case {tag_value} => {member.type}.decode(structureBytes, streamPositionHead).asInstanceOf[Try[{group_name}]]\n"

    s += f"      case _ => Success({group_name}_RawData(tag, structureBytes))\n"
    s += "    }\n"
    s += "  }\n\n"
    s += f"  def fromBytes(bytes: Array[Byte]): {group_name} =\n"
    s += "    decode(bytes, 0L).get\n\n"

    # Add JSON deserialization support for groups
    s += "  // JSON deserialization - dispatches based on _type field in JSON\n"
    s += f"  def decodeFromJson(json: String): {group_name} = {{\n"
    s += "    val jValue = parse(json)\n"
    s += "    decodeFromJValue(jValue)\n"
    s += "  }\n\n"
    s += f"  def decodeFromJValue(jValue: JValue): {group_name} = {{\n"
    s += "    // Extract _type discriminator field\n"
    s += '    val typeName = (jValue \\ "_type").extractOpt[String]\n'
    s += "    val jsonStr = compact(render(jValue))\n"
    s += "    typeName match {\n"

    for member in sorted(group.members, key=lambda m: m.value):
        s += f'      case Some("{member.type}") => {member.type}.deserialize(jsonStr).asInstanceOf[{group_name}]\n'

    # Add handling for RawData fallback
    s += f'      case Some("{group_name}_RawData") =>\n'
    s += f"        val j = Serialization.read[{group_name}_RawDataJson](jsonStr)\n"
    s += f"        {group_name}_RawData(j.tag, j.rawBytes.grouped(2).map(s => Integer.parseInt(s, 16).toByte).toArray)\n"
    s += '      case Some(unknown) => throw new Exception(s"Unknown type: $unknown")\n'
    s += '      case None => throw new Exception("Missing _type field in JSON")\n'
    s += "    }\n"
    s += "  }\n"
    s += "}\n\n"
    return s


def _get_structure_fields(
    type_name: str,
    definitions: dict[str, DefinedType],
) -> dict[str, tuple[str, int]] | None:
    """Get fields from a structure as {name: (type, size)} dict, or None if invalid."""
    if type_name not in definitions:
        return None
    structure = definitions[type_name]
    if not hasattr(structure, "members"):
        return None
    return {m.name: (m.type, m.size) for m in structure.members}


def find_common_fields(
    group: Group,
    definitions: dict[str, DefinedType],
) -> list[tuple[str, str, int]]:
    """Find fields that are common to all members of a group.

    Returns a list of (field_name, field_type, field_size) tuples for fields that:
    1. Exist in ALL member structures
    2. Have the same type AND size in all members

    This allows generating abstract methods in the sealed trait.
    """
    if not group.members:
        return []

    # Get the first member's fields as the baseline
    candidate_fields = _get_structure_fields(group.members[0].type, definitions)
    if candidate_fields is None:
        return []

    # Check all other members - keep only fields that exist with same type AND size
    for group_member in group.members[1:]:
        member_fields = _get_structure_fields(group_member.type, definitions)
        if member_fields is None:
            return []

        # Keep only fields that match in both name and (type, size)
        candidate_fields = {
            name: type_size
            for name, type_size in candidate_fields.items()
            if member_fields.get(name) == type_size
        }

    # Return as list of tuples (name, type, size), sorted by field name
    return sorted(
        [
            (name, type_, size)
            for name, (type_, size) in candidate_fields.items()
        ]
    )


def _get_default_value_for_type(scala_type: str) -> str:
    """Return a default value expression for a Scala type."""
    defaults = {
        "Array[Byte]": "Array.empty[Byte]",
        "Int": "0",
        "Short": "0",
        "Byte": "0",
        "Long": "0L",
        "Boolean": "false",
        "String": '""',
    }
    return defaults.get(scala_type, f"null.asInstanceOf[{scala_type}]")


def _render_group_trait(
    group_name: str,
    common_fields: list[tuple[str, str, int]],
    definitions: dict[str, DefinedType],
) -> str:
    """Render the sealed trait declaration for a group."""
    if not common_fields:
        return f"sealed trait {group_name} extends ByteSequence\n\n"

    lines = [f"sealed trait {group_name} extends ByteSequence {{"]
    for field_name, field_type, field_size in common_fields:
        scala_type = scala_type_for_member(field_type, field_size, definitions)
        if field_type in definitions:
            scala_type = field_type
        lines.append(f"  def {field_name}: {scala_type}")
    lines.append("}\n")
    return "\n".join(lines) + "\n"


def _render_raw_data_class(
    group_name: str,
    group_size: int,
    common_fields: list[tuple[str, str, int]],
    definitions: dict[str, DefinedType],
) -> str:
    """Render the RawData fallback case class for unrecognized tags."""
    s = f"/** Fallback for unrecognized tags in {group_name} group - preserves raw bytes */\n"
    s += f"final case class {group_name}_RawData(\n"
    s += "  tag: Int,\n"
    s += "  rawBytes: Array[Byte]\n"
    s += f") extends {group_name} with CustomJsonSerializer {{\n"
    s += f"  override def SizeInBytes: Int = rawBytes.length + {group_size}\n"
    s += (
        "  override def toByteSeq: Try[Seq[Byte]] = Success(rawBytes.toSeq)\n\n"
    )
    s += f"  type ObjectToSerialize = {group_name}_RawDataJson\n"
    s += f"  protected def getObjectToSerialize(): {group_name}_RawDataJson = "
    s += f"{group_name}_RawDataJson(tag, rawBytes)\n"

    for field_name, field_type, field_size in common_fields:
        scala_type = scala_type_for_member(field_type, field_size, definitions)
        if field_type in definitions:
            scala_type = field_type
        default = _get_default_value_for_type(scala_type)
        s += f"  override def {field_name}: {scala_type} = {default}\n"

    s += "}\n\n"

    # JSON helper class
    s += f"case class {group_name}_RawDataJson(\n"
    s += "  tag: Int,\n"
    s += "  rawBytes: Array[Byte]\n"
    s += ") {\n"
    s += f'  val groupType: String = "{group_name}"\n'
    s += '  val tagHex: String = f"0x${tag}%02X"\n'
    s += "}\n\n"
    return s


def _render_group_decoder(group_name: str, group: Group) -> str:
    """Render the decode object for a group."""
    tag_readers = {
        BYTES_1: "    val tag = bytes(0) & 0xFF\n",
        BYTES_2: "    val tag = BinaryUtils.bytesToUint16LE(bytes, 0)\n",
        BYTES_4: "    val tag = BinaryUtils.bytesToUint32LE(bytes, 0).toInt\n",
    }

    s = f"object {group_name} {{\n"
    s += f"  def decode(bytes: Array[Byte], streamPositionHead: Long): Try[{group_name}] = {{\n"
    s += f'    if (bytes.length < {group.size}) return Failure(new Exception("Insufficient bytes for tag"))\n'
    s += tag_readers.get(
        group.size, f"    val tag = bytes({group.size - 1}) & 0xFF\n"
    )
    s += f"    val structureBytes = bytes.drop({group.size})\n"
    s += "    tag match {\n"

    for member in sorted(group.members, key=lambda m: m.value):
        tag_value = format_large_int(member.value)
        s += f"case {tag_value} => {member.type}.decode(structureBytes, streamPositionHead).asInstanceOf[Try[{group_name}]]\n"

    s += f"      case _ => Success({group_name}_RawData(tag, structureBytes))\n"
    s += "    }\n"
    s += "  }\n\n"
    s += f"  def fromBytes(bytes: Array[Byte]): {group_name} =\n"
    s += "    decode(bytes, 0L).get\n"
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

    common_fields = find_common_fields(group, definitions)

    s = f"// {group.display_name}\n"
    s += f"// {group.description}\n"
    s += _render_group_trait(group_name, common_fields, definitions)
    s += _render_raw_data_class(
        group_name, group.size, common_fields, definitions
    )
    s += _render_group_decoder(group_name, group)

    for member in group.members:
        if member.type not in rendered:
            s += render_structure_with_group(
                member.type, definitions, templates, group_name
            )

    return s


def render_structure_with_group(
    structure_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
    group_name: str,
) -> str:
    """Render a structure that extends a group trait with JSON round-trip."""
    if structure_name in rendered:
        return ""
    rendered.add(structure_name)
    # Delegate to render_structure with group_name as the base trait
    return render_structure(
        structure_name, definitions, templates, extends_trait=group_name
    )


def render_bit_field(  # noqa: C901, PLR0912, PLR0915
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
    read_funcs = {
        BITS_8: "bytesToUint8LE",
        BITS_16: "bytesToUint16LE",
        BITS_32: "bytesToUint32LE",
        BITS_64: "bytesToUint64LE",
    }
    write_funcs = {
        BITS_8: "uint8LEtoBytes",
        BITS_16: "uint16LEtoBytes",
        BITS_32: "uint32LEtoBytes",
        BITS_64: "uint64LEtoBytes",
    }
    read_func = read_funcs.get(bits, "bytesToUint32LE")
    write_func = write_funcs.get(bits, "uint32LEtoBytes")

    # Build case class
    s += f"// {bit_field_dict['display_name']}\n"
    s += f"// {bit_field_dict['description']}\n"
    s += f"final case class {bit_field_name}(\n"

    # Generate fields (excluding reserved)
    member_lines = []
    for member in bit_field_dict.get("members", []):
        if member["type"] == "reserved":
            last_bit = member["start"] + member["bits"] - 1
            s += f"  // Reserved: bits {member['start']}-{last_bit}\n"
        else:
            scala_type = "Int"  # Bit fields are typically small enough for Int
            if member["type"] == "bool":
                scala_type = "Boolean" if member["bits"] == 1 else "Int"
            member_lines.append(f"  {member['name']}: {scala_type},")

    s += "\n".join(member_lines)
    s += "\n) extends ByteSequence with CustomJsonSerializer {\n"
    s += f"  override def SizeInBytes: Int = {bit_field_name}.SizeInBytes\n"
    s += f"  override def toByteSeq: Try[Seq[Byte]] = {bit_field_name}.encode(this)\n"
    s += "\n"
    s += "  // JSON serialization - convert to JSON-friendly intermediate form with type discriminator\n"
    s += f"  type ObjectToSerialize = {bit_field_name}Json\n"
    s += f"  protected def getObjectToSerialize(): {bit_field_name}Json = {bit_field_name}Json(\n"
    s += f'    _type = "{bit_field_name}",\n'
    # Generate conversion for each non-reserved member
    for member in bit_field_dict.get("members", []):
        if member["type"] == "reserved":
            continue
        s += f"    {member['name']} = {member['name']},\n"
    s += "  )\n"
    s += "}\n\n"

    # Generate JSON intermediate case class for serialization/deserialization
    s += f"// JSON intermediate class for {bit_field_name} serialization/deserialization\n"
    s += f"case class {bit_field_name}Json(\n"
    s += "  _type: String,\n"  # Type discriminator field
    json_field_lines = []
    for member in bit_field_dict.get("members", []):
        if member["type"] == "reserved":
            continue
        if member["type"] == "bool" and member["bits"] == 1:
            json_field_lines.append(f"  {member['name']}: Boolean")
        else:
            json_field_lines.append(f"  {member['name']}: Int")
    s += ",\n".join(json_field_lines)
    s += "\n)\n\n"

    # Generate companion object with CustomJsonDeserializer
    s += f"object {bit_field_name} extends ByteSequenceCodec[{bit_field_name}] with CustomJsonDeserializer[{bit_field_name}] {{\n"
    s += f"  final val SizeInBytes = {bit_field_dict['size']}\n\n"

    s += f"  override def decode(bytes: Array[Byte], streamPositionHead: Long): Try[{bit_field_name}] = Try {{\n"
    s += "    fromBytes(bytes)\n"
    s += "  }\n\n"

    s += f"  override def encode(event: {bit_field_name}): Try[Seq[Byte]] = Try {{\n"
    s += "    toBytes(event)\n"
    s += "  }\n\n"

    # Generate fromBytes
    s += f"  def fromBytes(bytes: Array[Byte]): {bit_field_name} = {{\n"
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

    # Generate toBytes
    scala_raw_type = {8: "Int", 16: "Int", 32: "Int", 64: "Long"}.get(
        bits, "Int"
    )
    s += f"  def toBytes(value: {bit_field_name}): Seq[Byte] = {{\n"
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

    # All write functions work with the rawBits directly
    s += f"    BinaryUtils.{write_func}(rawBits).toSeq\n"
    s += "  }\n\n"

    # Generate fromJson (JSON deserialization)
    s += "  // JSON deserialization\n"
    s += f"  override protected def fromJson(json: String)(implicit formats: Formats): {bit_field_name} = {{\n"
    s += f"    val j = Serialization.read[{bit_field_name}Json](json)\n"
    s += f"    {bit_field_name}(\n"
    for member in bit_field_dict.get("members", []):
        if member["type"] == "reserved":
            continue
        s += f"      {member['name']} = j.{member['name']},\n"
    s += "    )\n"
    s += "  }\n"
    s += "}\n\n"

    return s
