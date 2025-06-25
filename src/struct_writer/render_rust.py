import logging

from struct_writer.struct_parse import struct_parse
from struct_writer.templating import Template

_logger = logging.getLogger(__name__)

rendered = {"file"}


def render_file(definitions, templates, output_file) -> str:
    rendered.clear()
    rendered.add("file")

    s = ""
    s += Template(templates["file"]["description"]).safe_render(
        file=definitions.get("file", "")
    )
    s += Template(templates["file"]["header"]).safe_render(out_file=output_file)
    s += render_definitions(definitions, templates)
    s += Template(templates["file"]["footer"]).safe_render(out_file=output_file)
    return s


def render_definitions(definitions, templates):
    s = ""
    element_names = sorted(definitions.keys())

    group_names = {
        k for k, v in definitions.items() if "group" == v.get("type")
    }
    for element_name in group_names:
        s += render_definition(element_name, definitions, templates)

    for element_name in element_names:
        s += render_definition(element_name, definitions, templates)
    return s


def render_definition(element_name, definitions, templates):
    if element_name in rendered:
        return ""
    rendered.add(element_name)
    definition = definitions[element_name]
    s = ""
    if "structure" == definition["type"]:
        s += render_structure(element_name, definitions, templates)
    if "enum" == definition["type"]:
        s += render_enum(element_name, definitions, templates)
    if "group" == definition["type"]:
        s += render_group(element_name, definitions, templates)
    if "bit_field" == definition["type"]:
        s += render_bit_field(element_name, definitions, templates)

    return s


def render_structure(structure_name, definitions, templates):
    structure = definitions[structure_name]
    assert structure["type"] == "structure"
    structure["name"] = structure_name
    expected_size = structure["size"]
    measured_size = 0
    s = ""

    if members := structure.get("members"):
        for member in members:
            try:
                measured_size += member["size"]
            except KeyError:  # pragma: no cover
                _logger.error("Failed to render structure `%s`", structure_name)
                _logger.error(
                    "Member `%s` is missing `size` attriute", member["name"]
                )
                raise
            member_name = member["type"]
            if member_name in definitions:
                s += render_definition(member_name, definitions, templates)

    structure["serialization"] = render_structure_serialization(
        structure, templates
    )
    structure["deserialization"] = render_structure_deserialization(
        structure, templates
    )

    s += Template(templates["structure"]["header"]).safe_render(
        structure=structure
    )
    s += render_structure_members(structure, templates)
    s += Template(templates["structure"]["footer"]).safe_render(
        structure=structure
    )

    assert expected_size == measured_size, (
        f"Structure `{structure_name}` size is {expected_size}, but member sizes total {measured_size}"
    )
    return s


def render_structure_serialization(structure, templates):
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


def render_structure_deserialization(structure, templates):
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


def render_structure_members(structure, templates):
    s = ""
    assert structure["type"] == "structure"
    if members := structure.get("members"):
        for member in members:
            s += render_structure_member(member, templates)
    else:
        s = templates["structure"]["members"]["empty"]["definition"]
    return s


def render_structure_member(member, templates):
    member_templates = templates["structure"]["members"].get(
        member["type"], templates["structure"]["members"]["default"]
    )
    member_template = member_templates["definition"]
    s = Template(member_template).safe_render(member=member)
    return s


def render_enum(element_name, definitions, templates):
    enumeration = definitions[element_name]
    assert enumeration["type"] == "enum"
    enumeration["name"] = element_name
    enumeration["repr_type"] = enum_repr_type(enumeration)
    enumeration = struct_parse.complete_enums(enumeration)
    enumeration["unsigned_header"] = (
        templates["enum"]["unsigned_header"]
        if not enum_is_signed(enumeration)
        else ""
    )

    enumeration["matches"] = enum_matches(enumeration)

    s = ""

    s += Template(templates["enum"]["header"]).safe_render(
        enumeration=enumeration
    )
    s += render_enum_values(element_name, definitions, templates)
    s += Template(templates["enum"]["footer"]).safe_render(
        enumeration=enumeration
    )

    return s


def enum_repr_type(enumeration):
    signed = "i" if enum_is_signed(enumeration) else "u"
    bits = enumeration["size"] * 8
    repr_type = f"{signed}{bits}"
    return repr_type


def enum_is_signed(enumeration):
    return any(v.get("value", 0) < 0 for v in enumeration.get("values", []))


def enum_matches(enumeration):
    match_lines = [
        f"{v['value']} => Ok({enumeration['name']}::{v['label']}),"
        for v in enumeration.get("values", [])
    ]
    s = "\n".join(match_lines)
    return s


def render_enum_values(element_name, definitions, templates):
    enumeration = definitions[element_name]
    enumeration["name"] = element_name
    s = ""
    values = enumeration.get("values")
    for value in values:
        s += render_enum_value(value, enumeration, templates)
    return s


def render_enum_value(value_definition, enumeration, templates):
    assert "value" in value_definition
    return Template(templates["enum"]["valued"]).safe_render(
        enumeration=enumeration, value=value_definition
    )


def render_group(group_name, definitions, templates):
    group = definitions[group_name]
    assert group["type"] == "group"
    group["name"] = group_name
    s = ""

    group_elements = {
        k: v
        for k, v in definitions.items()
        if group_name in v.get("groups", {})
    }
    group_elements = dict(
        sorted(
            group_elements.items(),
            key=lambda x: x[1]["groups"][group_name]["value"],
        )
    )

    if not group_elements:
        return ""

    try:
        enum_size = group["size"]
    except KeyError:  # pragma: no cover
        _logger.error("Group `%s` is missing `size`", group_name)
        raise

    union_size = max(v["size"] for v in group_elements.values())
    type_size = enum_size + union_size
    repr_type = f"u{enum_size * 8}"
    group["repr_type"] = repr_type
    group["max_size"] = type_size

    s += Template(templates["group"]["header"]).safe_render(group=group)

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

    for k, v in group_elements.items():
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

    for k, v in group_elements.items():
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
assert!(value.len() >= {enum_size});
let repr_int = {repr_type}::from_le_bytes(value[0..{enum_size}].try_into().unwrap());
match repr_int {{
"""

    for k, v in group_elements.items():
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


def render_bit_field(bit_field_name, definitions, templates):
    bit_field = definitions[bit_field_name]
    assert bit_field["type"] == "bit_field"
    bit_field["name"] = bit_field_name
    s = ""

    members = bit_field["members"]
    for member in members:
        member_name = member["type"]
        if member_name in definitions:
            s += render_definition(member_name, definitions, templates)

    s += Template(templates["bit_field"]["header"]).safe_render(
        bit_field=bit_field
    )
    s += render_bit_field_members(bit_field_name, definitions, templates)
    s += Template(templates["bit_field"]["footer"]).safe_render(
        bit_field=bit_field
    )

    return s


def render_bit_field_members(bit_field_name, definitions, templates):
    bit_field = definitions.get(bit_field_name)

    s = ""
    assert bit_field["type"] == "bit_field"
    members = bit_field["members"]
    bit_position = 0
    for member in members:
        assert bit_position <= member["start"]
        member = struct_parse.complete_bit_field_member(member)
        if member["start"] == bit_position:
            s += render_bit_field_member(bit_field, member, templates)
        else:
            s += render_bit_field_reserve(
                bit_position, bit_field, member["start"] - 1, templates
            )
            s += render_bit_field_member(bit_field, member, templates)
        bit_position = member["last"] + 1
    total_bits = bit_field["size"] * 8
    if bit_position < total_bits:
        last_bit = total_bits - 1
        s += render_bit_field_reserve(
            bit_position, bit_field, last_bit, templates
        )
        bit_position += last_bit - bit_position + 1
    assert bit_position == total_bits, f"{bit_position} != {total_bits}"
    return s


def render_bit_field_reserve(bit_position, bit_field, last_bit, templates):
    reserved_member = {
        "name": "reserved",
        "start": bit_position,
        "last": last_bit,
        "type": "reserved",
    }
    struct_parse.complete_bit_field_member(reserved_member)
    return render_bit_field_member(bit_field, reserved_member, templates)


def render_bit_field_member(bit_field, member, templates):
    if member_template := templates["bit_field"]["members"].get(member["type"]):
        return Template(member_template).safe_render(
            bit_field=bit_field, member=member
        )
    member_template = templates["bit_field"]["members"]["default"]
    return Template(member_template).safe_render(
        bit_field=bit_field, member=member
    )
