import json
import logging
import tomllib
from pathlib import Path

import click
import yaml
from rich.traceback import install

from structured_api import Group, Structure

_logger = logging.getLogger(__name__)

install()

rendered = set()


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
    "-o",
    "--output_file",
    prompt=True,
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
def main(input_definition: Path, output_file: Path):
    definitions = load_markup_file(input_definition)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        render_file(f, definitions)


def render_file(f, elements: dict[str, any]):
    file_info = elements["file"]
    f.write(file_info["header"])
    for name in elements.keys():
        render_element(f, name, elements)
    f.write(file_info["footer"])


def render_element(f, element: str, elements: dict[str, any]):
    if element not in elements:
        _logger.warning("Unable to render %s", element)
        return
    if element in rendered:
        return
    rendered.add(element)

    definition = elements[element]
    try:
        element_type = definition["type"]
    except KeyError as exc:
        raise KeyError(f"No `type` for `{element}`") from exc

    # if "enum" == element_type:
    #     e = Enumeration.from_dict({element: definition})
    #     f.write(e.render())
    if "structure" == element_type:
        s = Structure.from_dict({element: definition})
        f.write(s.render())
    if "group" == element_type:
        g = Group.from_dict({element: definition})
        for member in g.members.values():
            render_element(f, member.type, elements)
        f.write(g.render())


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
