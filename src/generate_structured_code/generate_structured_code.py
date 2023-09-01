import json
import tomllib
from pathlib import Path

import click
import yaml
from rich.traceback import install

from structured_api import Structure
from structured_api.group import Group

install()

rendered = {}


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
        f.write("#include <stdint.h>\n\n")
        for name in definitions.keys():
            f.write(render_element(name, definitions))
            f.write("\n")


def render_element(element: str, elements: dict[str, any]):
    if element in rendered:
        return ""

    definition = elements[element]
    try:
        element_type = definition["type"]
    except KeyError as exc:
        raise KeyError(f"No `type` for `{element}`") from exc

    if "structure" == element_type:
        s = Structure.from_dict({element: definition})
        return s.render()
    if "group" == element_type:
        g = Group.from_dict({element: definition})
        return g.render()
    return ""


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
