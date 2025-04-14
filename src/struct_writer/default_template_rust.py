import tomllib
from pathlib import Path


def default_template():
    template = Path(__file__).parent / "../../examples/template_rust.toml"
    template = template.absolute()
    template = tomllib.loads(template.read_text("utf-8"))
    return template
