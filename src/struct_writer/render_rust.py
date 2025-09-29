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
from struct_writer.struct_parse import struct_parse
from struct_writer.templating import Template

_logger = logging.getLogger(__name__)

rendered = {"file"}


def render_file(
    definitions: dict[str, Any],
    templates: dict[str, Any],
    output_file: Path,
) -> str:
    rendered.clear()
    rendered.add("file")

    parsed_definitions = TypeDefinitions.from_dict(definitions)

    s = ""
    s += Template(templates["file"]["description"]).safe_render(
        file=parsed_definitions.file_info
    )
    s += Template(templates["file"]["header"]).safe_render(out_file=output_file)
    s += render_definitions(parsed_definitions, templates)
    s += Template(templates["file"]["footer"]).safe_render(out_file=output_file)
    return s


def render_definitions(
    definitions: TypeDefinitions,
    templates: dict[str, Any],
) -> str:
    s = ""
    element_names = sorted(definitions.definitions.keys())

    group_names = {
        k for k, v in definitions.definitions.items() if isinstance(v, Group)
    }
    for element_name in group_names:
        s += render_definition(element_name, definitions.definitions, templates)

    for element_name in element_names:
        s += render_definition(element_name, definitions.definitions, templates)
    return s


def render_definition(
    element_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
) -> str:
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


def render_structure(
    structure_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
) -> str:
    structure = definitions[structure_name].as_structure()
    expected_size = structure.size
    measured_size = 0
    s = ""

    if members := structure.members:
        for member in members:
            measured_size += member.size
            member_name = member.type
            if member_name in definitions:
                s += render_definition(member_name, definitions, templates)

    structure_dict = structure.to_dict()

    structure_dict["serialization"] = render_structure_serialization(
        structure_dict, templates
    )
    structure_dict["deserialization"] = render_structure_deserialization(
        structure_dict, templates
    )

    s += Template(templates["structure"]["header"]).safe_render(
        structure=structure_dict
    )
    s += render_structure_members(structure_dict, templates)
    s += Template(templates["structure"]["footer"]).safe_render(
        structure=structure_dict
    )

    assert expected_size == measured_size, (
        f"Structure `{structure_name}` size is {expected_size}, but member sizes total {measured_size}"
    )
    return s


def render_structure_serialization(
    structure: dict[str, Any],
    templates: dict[str, Any],
) -> str:
    serialization_lines = []
    start = 0
    for member in structure.get("members", []):
        end = start + member["size"]
        buffer = {"start": start, "end": end}
        member_templates = templates["structure"]["members"].get(
            member["type"], templates["structure"]["members"]["default"]
        )
        member_template = member_templates["serialize"]
        s = Template(member_template).safe_render(member=member, buffer=buffer)

        serialization_lines.append(s)
        start = end

    return "\n".join(serialization_lines)


def render_structure_deserialization(
    structure: dict[str, Any],
    templates: dict[str, Any],
) -> str:
    serialization_lines = []
    start = 0
    for member in structure.get("members", []):
        end = start + member["size"]
        buffer = {"start": start, "end": end}
        member_templates = templates["structure"]["members"].get(
            member["type"], templates["structure"]["members"]["default"]
        )
        member_template = member_templates["deserialize"]
        s = Template(member_template).safe_render(member=member, buffer=buffer)

        serialization_lines.append(s)
        start = end

    return "\n".join(serialization_lines)


def render_structure_members(
    structure: dict[str, Any],
    templates: dict[str, Any],
) -> str:
    s = ""
    assert structure["type"] == "structure"
    if members := structure.get("members"):
        for member in members:
            s += render_structure_member(member, templates)
    else:
        s = templates["structure"]["members"]["empty"]["definition"]
    return s


def render_structure_member(
    member: dict[str, Any],
    templates: dict[str, Any],
) -> str:
    member_templates = templates["structure"]["members"].get(
        member["type"], templates["structure"]["members"]["default"]
    )
    member_template = member_templates["definition"]
    return Template(member_template).safe_render(member=member)


def render_enum(
    element_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
) -> str:
    enumeration = definitions[element_name]

    enumeration_dict = enumeration.to_dict()

    enumeration_dict["repr_type"] = enum_repr_type(enumeration_dict)
    enumeration_dict = struct_parse.complete_enums(enumeration_dict)

    enumeration_dict["matches"] = enum_matches(enumeration_dict)

    s = ""

    s += Template(templates["enum"]["header"]).safe_render(
        enumeration=enumeration_dict
    )
    s += render_enum_values(element_name, definitions, templates)
    s += Template(templates["enum"]["footer"]).safe_render(
        enumeration=enumeration_dict
    )

    return s


def enum_repr_type(enumeration: dict[str, Any]) -> str:
    signed = "i" if enum_is_signed(enumeration) else "u"
    bits = enumeration["size"] * 8
    return f"{signed}{bits}"


def enum_is_signed(enumeration: dict[str, Any]) -> bool:
    return any(v.get("value", 0) < 0 for v in enumeration.get("values", []))


def enum_matches(enumeration: dict[str, Any]) -> str:
    match_lines = [
        f"{v['value']} => Ok({enumeration['name']}::{v['label']}),"
        for v in enumeration.get("values", [])
    ]
    return "\n".join(match_lines)


def render_enum_values(
    element_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
) -> str:
    enumeration = definitions[element_name]

    enumeration_dict = enumeration.to_dict()

    s = ""
    values = enumeration_dict.get("values", [])
    for value in values:
        s += render_enum_value(value, enumeration_dict, templates)
    return s


def render_enum_value(
    value_definition: dict[str, Any],
    enumeration: dict[str, Any],
    templates: dict[str, Any],
) -> str:
    assert "value" in value_definition
    return Template(templates["enum"]["valued"]).safe_render(
        enumeration=enumeration, value=value_definition
    )


def render_group(  # noqa: PLR0915
    group_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
) -> str:
    group = definitions[group_name].as_group()
    s = ""

    if not group.members:
        return ""

    # Build group_elements dictionary for template compatibility
    group_elements = {}
    for member in group.members:
        member_def = definitions[member.type]
        group_elements[member.type] = {
            "size": member_def.size,
            "description": member_def.description,
            "display_name": member_def.display_name,
            "type": member_def.__class__.__name__.lower(),
            "groups": {
                group_name: {
                    "name": member.name,
                    "value": member.value,
                }
            },
        }

    group_elements = dict(
        sorted(
            group_elements.items(),
            key=lambda x: x[1]["groups"][group_name]["value"],
        )
    )

    enum_size = group.size
    union_size = max(v["size"] for v in group_elements.values())
    type_size = enum_size + union_size
    repr_type = f"u{enum_size * 8}"

    group_dict = group.to_dict()
    group_dict["repr_type"] = repr_type
    group_dict["max_size"] = type_size

    s += Template(templates["group"]["header"]).safe_render(group=group_dict)

    for k, v in group_elements.items():
        name = v["groups"][group_name]["name"]
        value = v["groups"][group_name]["value"]
        s += f"{name}({k}) = {value},\n"

    s += "}\n"

    s += f"""\
impl {group_name} {{
pub fn size(&self) -> usize {{
match self{{
"""

    for v in group_elements.values():
        name = v["groups"][group_name]["name"]
        payload_size = v["size"]
        s += f"{group_name}::{name}(_) => {enum_size + payload_size},\n"

    s += """\
}
}
"""

    s += f"""pub fn size_from_tag(tag: {repr_type}) -> Option<usize> {{
match tag {{
"""

    for v in group_elements.values():
        name = v["groups"][group_name]["name"]
        tag_value = v["groups"][group_name]["value"]
        payload_size = v["size"]
        total_size = enum_size + payload_size
        s += (
            f"{tag_value:#04x} => Some({total_size}), // {group_name}::{name}\n"
        )
    s += " _ => None,"
    s += """\
}
}
}
"""

    s += f"""\
impl From<{group_name}> for {group_name}_slice {{
fn from(value: {group_name}) -> Self {{
#[allow(unused_mut)]
let mut buf = [0_u8; {type_size}];
match value {{
"""

    for k, v in group_elements.items():
        name = v["groups"][group_name]["name"]
        value = v["groups"][group_name]["value"]
        inner_size = v["size"]
        end = enum_size + inner_size
        s += f"{group_name}::{name}(inner) => {{\n"
        s += f"buf[0..{enum_size}].copy_from_slice(&{value}_{repr_type}.to_le_bytes());\n"
        s += f"let inner_buf: {k}_slice = inner.into();\n"
        s += f"buf[{enum_size}..{end}].copy_from_slice(&inner_buf);\n"
        s += "}\n"

    s += """\
}
buf
}
}
"""

    s += f"""\
impl TryFrom<&[u8]> for {group_name} {{
type Error = ();

fn try_from(value: &[u8]) -> Result<Self, Self::Error> {{
if !(value.len() >= {enum_size}) {{return Err(());}}
let repr_int = {repr_type}::from_le_bytes(value[0..{enum_size}]
.try_into()
.unwrap());
match repr_int {{
"""

    for v in group_elements.values():
        name = v["groups"][group_name]["name"]
        value = v["groups"][group_name]["value"]
        inner_size = v["size"]
        end = enum_size + inner_size
        s += f"{value} => {{\n"
        s += f"let inner_buf: &[u8] = &value[{enum_size}..];\n"
        s += "let inner = inner_buf.try_into()?;\n"
        s += f"Ok({group_name}::{name}(inner))\n"
        s += "}\n"

    s += f"""\
_ => Err(()),
}}
}}
}}

impl TryFrom<{group_name}_slice> for {group_name} {{
type Error = ();

fn try_from(value: {group_name}_slice) -> Result<Self, Self::Error> {{
let r: &[u8] = &value;
r.try_into()
}}
}}
"""

    return s


def render_bit_field(
    bit_field_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
) -> str:
    bit_field = definitions[bit_field_name].as_bit_field()
    s = ""

    members = bit_field.members
    for member in members:
        member_name = member.type
        if member_name in definitions:
            s += render_definition(member_name, definitions, templates)

    bit_field_dict = bit_field.to_dict()

    bit_field_dict["serialization"] = render_bit_field_serialization(
        bit_field_dict, templates
    )

    bit_field_dict["deserialization"] = render_bit_field_deserialization(
        bit_field_dict, templates
    )

    s += Template(templates["bit_field"]["header"]).safe_render(
        bit_field=bit_field_dict
    )
    s += render_bit_field_members(bit_field_name, definitions, templates)
    s += Template(templates["bit_field"]["footer"]).safe_render(
        bit_field=bit_field_dict
    )

    return s


def render_bit_field_members(
    bit_field_name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
) -> str:
    bit_field = definitions[bit_field_name].as_bit_field()
    bit_field_dict = bit_field.to_dict()

    s = ""
    members = bit_field_dict.get("members", [])
    for member in members:
        s += render_bit_field_member(bit_field_dict, member, templates)
    return s


def render_bit_field_member(
    bit_field: dict[str, Any],
    member: dict[str, str | int],
    templates: dict[str, Any],
) -> str:
    if member_template := templates["bit_field"]["members"].get(member["type"]):
        return Template(member_template).safe_render(
            bit_field=bit_field, member=member
        )
    member_template = templates["bit_field"]["members"]["default"]
    return Template(member_template).safe_render(
        bit_field=bit_field, member=member
    )


def render_bit_field_serialization(
    bit_field_dict: dict[str, Any],
    _templates: dict[str, Any],
) -> str:
    bit_field_type = f"u{8 * bit_field_dict['size']}"
    serialization_lines = []
    serialization_lines.append(f"let mut raw_bits = 0_{bit_field_type};")

    for member in bit_field_dict.get("members", []):
        mask = "0b" + "1" * member["bits"]
        shift = member["start"]
        s = ""
        match member["type"].lower():
            case "bool":
                s = f"raw_bits |=  (if input.{member['name']} {{1_{bit_field_type}}} else {{0_{bit_field_type}}} <<  {shift});"
                serialization_lines.append(s)
            case "int":
                pass
            case "uint":
                s = f"raw_bits |= ((input.{member['name']} as {bit_field_type}) & {mask}_{bit_field_type}) << {shift};"
                serialization_lines.append(s)
            case "reserved":
                continue
            case _:
                member_repr = f"u{member['size'] * 8}"
                s = f"let {member['name']}: {member['type']}_slice = input.{member['name']}.into();"
                serialization_lines.append(s)
                s = f"let {member['name']} = {member_repr}::from_le_bytes({member['name']}) as {bit_field_type};"
                serialization_lines.append(s)
                s = f"raw_bits |= (({member['name']}) & {mask}_{bit_field_type}) << {shift};"
                serialization_lines.append(s)

    serialization_lines.append("raw_bits.to_le_bytes()")
    return "\n".join(serialization_lines)


def render_bit_field_deserialization(
    bit_field_dict: dict[str, Any],
    _templates: dict[str, Any],
) -> str:
    bits = 8 * bit_field_dict["size"]
    bit_field_type = f"u{bits}"
    serialization_lines = []
    serialization_lines.append(
        f"let raw_bits = {bit_field_type}::from_le_bytes(input[0..{bit_field_dict['size']}].try_into().unwrap());"
    )
    serialization_lines.append("Ok(Self{")

    for member in bit_field_dict.get("members", []):
        mask = "0b" + "1" * member["bits"]
        shift = member["start"]
        member_repr = f"u{member['size'] * 8}"
        to_uint = f"(raw_bits >> {shift}) & {mask}_{bit_field_type}"
        s = f"{member['name']}: "
        match member["type"].lower():
            case "bool":
                s += f"({to_uint}) != 0"
            case "int":
                s += f"({to_uint}) as i{bits}"
            case "uint":
                s += f"({to_uint}) as {member_repr}"
            case "reserved":
                continue
            case _:
                member_repr = f"u{member['size'] * 8}"
                s += (
                    f"{member['type']}::try_from(({to_uint}) as {member_repr})?"
                )
        s += ","
        serialization_lines.append(s)

    serialization_lines.append("})")
    return "\n".join(serialization_lines)
