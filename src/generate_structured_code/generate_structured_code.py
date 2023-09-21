import json
import logging
import math
import tomllib
from pathlib import Path

import click
import yaml
from rich.traceback import install

from templating import Template

_logger = logging.getLogger(__name__)

install()

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
)
@click.option(
    "-t",
    "--template-file",
    prompt=True,
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
    prompt=True,
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
def main(input_definition: Path, template_file: Path, output_file: Path):
    definitions = load_markup_file(input_definition)
    templates = load_markup_file(template_file)

    with output_file.open("w", encoding="utf-8") as f:
        f.write(
            Template(templates["file"]["description"]).render(
                file=definitions["file"]
            )
        )
        f.write(
            Template(templates["file"]["header"]).render(out_file=output_file)
        )
        s = render_definitions(definitions, templates)
        f.write(s)
        f.write(
            Template(templates["file"]["footer"]).render(out_file=output_file)
        )


def render_definitions(definitions, templates):
    s = ""
    element_names = set(definitions.keys())
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
    structure["name"] = element_name
    s = ""

    s += Template(templates["structure"]["header"]).render(structure=structure)
    s += render_structure_members(element_name, definitions, templates)
    s += Template(templates["structure"]["footer"]).render(structure=structure)

    return s


def render_structure_members(element_name, definitions, templates):
    structure = definitions[element_name]
    s = ""
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
        return Template(member_template).render(member=member)
    member_template = templates["structure"]["members"]["default"]
    return Template(member_template).render(member=member)


def render_structure_union(union, templates):
    s = ""
    s += Template(templates["structure"]["members"]["union"]["header"]).render(
        union=union
    )

    for member in union["members"]:
        s += render_structure_member(member, templates)

    s += Template(templates["structure"]["members"]["union"]["footer"]).render(
        union=union
    )
    return s


def render_enum(element_name, definitions, templates):
    enumeration = definitions[element_name]
    enumeration["name"] = element_name
    s = ""

    s += Template(templates["enum"]["header"]).render(enumeration=enumeration)
    s += render_enum_values(element_name, definitions, templates)
    s += Template(templates["enum"]["footer"]).render(enumeration=enumeration)

    return s


def render_enum_values(element_name, definitions, templates):
    enumeration = definitions[element_name]
    enumeration["name"] = element_name
    s = ""
    if values := enumeration.get("values"):
        for value in values:
            s += render_enum_value(value, enumeration, templates)
    else:
        s = templates["enum"]["values"]["empty"]
    return s


def render_enum_value(value_definition, enumeration, templates):
    if "value" in value_definition:
        return Template(templates["enum"]["valued"]).render(
            enumeration=enumeration, value=value_definition
        )
    member_template = templates["enum"]["default"]
    return Template(member_template).render(
        enumeration=enumeration, value=value_definition
    )


def render_group(group_name, definitions, templates):
    group = definitions[group_name]
    group["name"] = group_name
    s = ""

    group_elements = {
        k: v
        for k, v in definitions.items()
        if group_name in v.get("groups", {})
    }

    group_enum = {
        "name": f'{group["name"]}_tag',
        "display_name": f'{group["name"]} tag',
        "description": f'Enumeration for {group["name"]} tag',
        "type": "enum",
        "size": int(math.log(len(group_elements), 256)) + 1,
    }
    group_enum["values"] = []
    for element_name, element in group_elements.items():
        element["name"] = element_name
        enum_value = {
            "label": element["groups"][group_name]["name"],
            "value": element["groups"][group_name]["value"],
            "display_name": element["description"],
            "description": "@see "
            + Template(templates["structure"]["type_name"]).render(
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


def load_markup_file(markup_file: Path):
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
