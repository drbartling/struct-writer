import logging

from struct_writer.struct_parse.struct_parse import complete_bit_field_member
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
    element_names = set(definitions.keys())

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

    s += Template(templates["structure"]["header"]).safe_render(
        structure=structure
    )
    s += render_structure_members(structure_name, definitions, templates)
    s += Template(templates["structure"]["footer"]).safe_render(
        structure=structure
    )

    assert expected_size == measured_size, (
        f"Structure `{structure_name}` size is {expected_size}, but member sizes total {measured_size}"
    )
    return s


def render_structure_members(structure_name, definitions, templates):
    structure = definitions.get(structure_name)

    s = ""
    assert structure["type"] == "structure"
    if members := structure.get("members"):
        for member in members:
            s += render_structure_member(member, templates)
    else:
        s = templates["structure"]["members"]["empty"]
    return s


def render_structure_member(member, templates):
    if "union" == member["type"]:
        return render_structure_union(member, templates)
    if member_template := templates["structure"]["members"].get(member["type"]):
        return Template(member_template).safe_render(member=member)
    member_template = templates["structure"]["members"]["default"]
    return Template(member_template).safe_render(member=member)


def render_structure_union(union, templates):
    s = ""
    s += Template(
        templates["structure"]["members"]["union"]["header"]
    ).safe_render(union=union)

    for member in union["members"]:
        s += render_structure_member(member, templates)

    s += Template(
        templates["structure"]["members"]["union"]["footer"]
    ).safe_render(union=union)
    return s


def render_enum(element_name, definitions, templates):
    enumeration = definitions[element_name]
    assert enumeration["type"] == "enum"
    enumeration["name"] = element_name
    s = ""

    s += Template(templates["enum"]["header"]).safe_render(
        enumeration=enumeration
    )
    s += render_enum_values(element_name, definitions, templates)
    s += Template(templates["enum"]["footer"]).safe_render(
        enumeration=enumeration
    )

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
    if "value" in value_definition:
        return Template(templates["enum"]["valued"]).safe_render(
            enumeration=enumeration, value=value_definition
        )
    member_template = templates["enum"]["default"]
    return Template(member_template).safe_render(
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

    group_enum = {
        "name": f"{group['name']}_tag",
        "display_name": f"{group['name']} tag",
        "description": f"Enumeration for {group['name']} tag",
        "type": "enum",
        "size": enum_size,
    }
    group_enum["values"] = []
    for element_name, element in group_elements.items():
        element["name"] = element_name
        enum_value = {
            "label": element["groups"][group_name]["name"],
            "value": element["groups"][group_name]["value"],
            "display_name": element["description"],
            "description": "@see "
            + Template(templates["structure"]["type_name"]).safe_render(
                structure=element
            ),
        }
        group_enum["values"].append(enum_value)

    definitions[group_enum["name"]] = group_enum
    s += render_definition(group_enum["name"], definitions, templates)

    for element_name in group_elements:
        s += render_definition(element_name, definitions, templates)

    group_struct = {
        "name": f"{group['name']}",
        "display_name": group["display_name"],
        "description": group["description"],
        "type": "structure",
        "size": -1,
    }
    group_struct["members"] = [
        {
            "name": "tag",
            "size": group_enum["size"],
            "type": group_enum["name"],
            "description": group_enum["display_name"],
        }
    ]
    group_union = {
        "name": "value",
        "type": "union",
        "description": "",
        "members": [],
    }
    for element_name, element in group_elements.items():
        element["name"] = element_name
        union_member = {
            "name": element["groups"][group_name]["name"],
            "type": element_name,
            "display_name": element["display_name"],
            "description": element["description"],
            "size": element["size"],
        }
        group_union["members"].append(union_member)
    group_union["size"] = max(m["size"] for m in group_union["members"])
    group_struct["members"].append(group_union)
    size = group_enum["size"] + group_union["size"]
    group_struct["size"] = size

    definitions[group_struct["name"]] = group_struct
    rendered.remove(group_struct["name"])
    s += render_definition(group_struct["name"], definitions, templates)

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
        member = complete_bit_field_member(member)
        if member["start"] == bit_position:
            s += render_bit_field_member(bit_field, member, templates)
        else:
            s += render_bit_field_reserve(
                bit_position, bit_field, member, templates
            )
            s += render_bit_field_member(bit_field, member, templates)
        bit_position = member["last"] + 1
    return s


def render_bit_field_reserve(bit_position, bit_field, member, templates):
    reserved_member = {
        "name": "reserved",
        "start": bit_position,
        "last": member["start"] - 1,
        "type": "reserved",
    }
    complete_bit_field_member(reserved_member)
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
