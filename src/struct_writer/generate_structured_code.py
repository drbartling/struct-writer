import json
import logging
import tomllib
from pathlib import Path

import click
import yaml
from rich.traceback import install

from struct_writer import templating
from struct_writer.default_template import default_template
from struct_writer.templating import Template

install()

_logger = logging.getLogger(__name__)

rendered = {"file"}


@click.command()
@click.option(
    "-i",
    "--input-definitions",
    prompt=True,
    multiple=True,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
    required=True,
)
@click.option(
    "-t",
    "--template-files",
    multiple=True,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
@click.option(
    "-o",
    "--output-file",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
def main(
    input_definitions: list[Path], template_files: list[Path], output_file: Path
):  # pragma: no cover
    definitions = {}
    for input_definition in input_definitions:
        definitions = templating.merge(
            definitions, load_markup_file(input_definition)
        )
    templates = default_template()
    for template_file in template_files:
        templates = templating.merge(templates, load_markup_file(template_file))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        f.write(
            Template(templates["file"]["description"]).safe_render(
                file=definitions.get("file", "")
            )
        )
        f.write(
            Template(templates["file"]["header"]).safe_render(
                out_file=output_file
            )
        )
        try:
            s = render_definitions(definitions, templates)
        except Exception:
            _logger.error(
                "Failed to render code from files `%s`", input_definitions
            )
            raise
        f.write(s)
        f.write(
            Template(templates["file"]["footer"]).safe_render(
                out_file=output_file
            )
        )


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
    if "union" == definition["type"]:
        s += render_union(element_name, definitions, templates)
    if "enum" == definition["type"]:
        s += render_enum(element_name, definitions, templates)
    if "group" == definition["type"]:
        s += render_group(element_name, definitions, templates)
    if "bit_field" == definition["type"]:
        s += render_bit_field(element_name, definitions, templates)

    return s


def render_union(union_name, definitions, templates):
    union = definitions[union_name]
    assert union["type"] == "union"
    union["name"] = union_name
    expected_size = union["size"]
    measured_size = 0
    s = ""

    if members := union.get("members"):
        for member in members:
            try:
                measured_size += member["size"]
            except KeyError:  # pragma: no cover
                _logger.error("Failed to render structure `%s`", union_name)
                _logger.error(
                    "Member `%s` is missing `size` attriute", member["name"]
                )
                raise
            member_name = member["type"]
            if member_name in definitions:
                s += render_definition(member_name, definitions, templates)

    s += Template(templates["union"]["header"]).safe_render(union=union)
    s += render_union_members(union_name, definitions, templates)
    s += Template(templates["union"]["footer"]).safe_render(union=union)

    assert (
        expected_size == measured_size
    ), f"Structure `{union_name}` size is {expected_size}, but member sizes total {measured_size}"
    return s


def render_union_members(union_name, definitions, templates):
    union = definitions.get(union_name)
    s = ""
    assert union["type"] == "union"
    if members := union.get("members"):
        for member in members:
            s += render_union_member(member, templates)
    else:
        try:
            s = templates["union"]["members"]["empty"]
        except KeyError:
            s = templates["structure"]["members"]["empty"]
    return s


def render_union_member(member, templates):
    try:
        member_template = templates["union"]["members"]["type"]
    except KeyError:
        pass
    else:
        return Template(member_template).safe_render(member=member)

    if member_template := templates["structure"]["members"].get(member["type"]):
        return Template(member_template).safe_render(member=member)
    try:
        member_template = templates["union"]["members"]["default"]
    except KeyError:
        member_template = templates["structure"]["members"]["default"]
    return Template(member_template).safe_render(member=member)


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

    assert (
        expected_size == measured_size
    ), f"Structure `{structure_name}` size is {expected_size}, but member sizes total {measured_size}"
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
    if member_template := templates["structure"]["members"].get(member["type"]):
        return Template(member_template).safe_render(member=member)
    member_template = templates["structure"]["members"]["default"]
    return Template(member_template).safe_render(member=member)


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
        "name": f'{group["name"]}_tag',
        "display_name": f'{group["name"]} tag',
        "description": f'Enumeration for {group["name"]} tag',
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

    group_union = {
        "name": f'{group["name"]}_union',
        "type": "union",
        "display_name": group["display_name"],
        "description": group["description"],
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
    definitions[group_union["name"]] = group_union
    s += render_definition(group_union["name"], definitions, templates)

    group_struct = {
        "name": f'{group["name"]}',
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
        },
        {
            "name": "value",
            "size": group_union["size"],
            "type": group_union["name"],
            "description": "Union of group structures",
        },
    ]
    size = group_enum["size"] + group_union["size"]
    print(f'{size} = {group_enum["size"]} + {group_union["size"]}')
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


def complete_bit_field_member(bit_field_member):
    try:
        assert "start" in bit_field_member
        assert 0 <= bit_field_member["start"]

        if "last" not in bit_field_member and "bits" not in bit_field_member:
            bit_field_member["bits"] = 1
            bit_field_member["last"] = bit_field_member["start"]
        if "last" not in bit_field_member:
            bit_field_member["last"] = (
                bit_field_member["start"] + bit_field_member["bits"] - 1
            )
        if "bits" not in bit_field_member:
            bit_field_member["bits"] = (
                bit_field_member["last"] - bit_field_member["start"] + 1
            )

        assert (
            bit_field_member["last"]
            == bit_field_member["start"] + bit_field_member["bits"] - 1
        )
        assert (
            bit_field_member["bits"]
            == bit_field_member["last"] - bit_field_member["start"] + 1
        )

        return bit_field_member
    except:  # pragma: no cover
        _logger.error(str(bit_field_member))
        raise


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


def load_markup_file(markup_file: Path):  # pragma: no cover
    extension = markup_file.suffix
    if ".toml" == extension:
        with markup_file.open("rb") as f:
            return tomllib.load(f)
    if ".json" == extension:
        with markup_file.open("rb") as f:
            return json.load(f)
    if extension in {".yml", ".yaml"}:
        with markup_file.open("rb") as f:
            return yaml.full_load(f)
    raise ValueError(f"Unsupported Extension: {extension}")


if __name__ == "__main__":  # pragma: no cover
    # Ignored missing parameter lint, since the click library passes the
    # arguments in from the command line for us
    main()  # pylint:disable=no-value-for-parameter
