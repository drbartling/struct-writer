import json
import logging
import tomllib
from pathlib import Path

import click
import yaml
from rich.traceback import install

from struct_writer import render_c, templating
from struct_writer.default_template_c import default_template

install()

_logger = logging.getLogger(__name__)


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

    try:
        s = render_c.render_file(definitions, templates, output_file)
    except Exception:
        _logger.error(
            "Failed to render code from file(s) `%s`", input_definitions
        )
        raise

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        f.write(s)


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
