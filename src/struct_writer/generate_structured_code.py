import json
import logging
import math
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
    "--input-definition",
    prompt=True,
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
    input_definition: Path, template_files: Path, output_file: Path
):  # pragma: no cover
    definitions = load_markup_file(input_definition)
    templates = default_template()
    for template_file in template_files:
        templates = templating.merge(templates, load_markup_file(template_file))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        f.write(
            Template(templates["file"]["description"]).safe_render(
                file=definitions["file"]
            )
        )
        f.write(
            Template(templates["file"]["header"]).safe_render(
                out_file=output_file
            )
        )
        s = render_definitions(definitions, templates)
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
    if "enum" == definition["type"]:
        s += render_enum(element_name, definitions, templates)
    if "group" == definition["type"]:
        s += render_group(element_name, definitions, templates)

    return s


def render_structure(element_name, definitions, templates):
    structure = definitions[element_name]
    assert structure["type"] == "structure"
    structure["name"] = element_name
    s = ""

    if members := structure.get("members"):
        for member in members:
            member_name = member["type"]
            if member_name in definitions:
                s += render_definition(member_name, definitions, templates)

    s += Template(templates["structure"]["header"]).safe_render(
        structure=structure
    )
    s += render_structure_members(element_name, definitions, templates)
    s += Template(templates["structure"]["footer"]).safe_render(
        structure=structure
    )

    return s


def render_structure_members(element_name, definitions, templates):
    structure = definitions.get(element_name)

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

    enum_size = int(math.log(len(group_elements), 256)) + 1

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

    group_struct = {
        "name": f'{group["name"]}_u',
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
    group_struct["members"].append(group_union)
    size = group_enum["size"] + max(m["size"] for m in group_union["members"])
    group_struct["size"] = size

    definitions[group_struct["name"]] = group_struct
    s += render_definition(group_struct["name"], definitions, templates)

    return s


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
