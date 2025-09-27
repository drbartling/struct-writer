from pathlib import Path
from typing import Any

from struct_writer import generate_structured_code


def default_template() -> dict[str, Any]:
    this_file = Path(__file__)
    this_dir = this_file.parent
    src_dir = this_dir.parent
    project_dir = src_dir.parent
    example_template = project_dir / "examples/template_rust.toml"
    return generate_structured_code.load_markup_file(example_template)
