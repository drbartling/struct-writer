from pathlib import Path

from struct_writer import (
    default_template_csv,
    generate_structured_code,
    render_csv,
)


def test_default_template_matches_example() -> None:
    this_path = Path(__file__).resolve()
    project_root = this_path / "../.."
    project_root = project_root.resolve()
    template_example = project_root / "examples/template_csv.toml"
    assert template_example.is_file()

    example_template = generate_structured_code.load_markup_file(
        template_example
    )
    default_template = default_template_csv.default_template()

    assert example_template == default_template


def test_render_empty_file() -> None:
    definitions = {
        "file": {
            "brief": "Command API docs",
            "description": "Auto generated docs",
        },
    }
    template = default_template_csv.default_template()
    result = render_csv.render_file(definitions, template, Path("docs.csv"))
    expected = """category,qualified_name,display_name,description,data_type,size_bytes,details\nfile,docs.csv,Command API docs,Auto generated docs,metadata,,\n"""
    assert result == expected


def test_render_structure_rows() -> None:
    definitions = {
        "file": {
            "brief": "Command API docs",
            "description": "Auto generated docs",
        },
        "cmd_temperature_set": {
            "description": "Request a change in temperature",
            "display_name": "Request temperature change",
            "size": 3,
            "type": "structure",
            "members": [
                {
                    "name": "temperature",
                    "size": 2,
                    "type": "int",
                    "description": "Desired temperature",
                },
                {
                    "name": "units",
                    "size": 1,
                    "type": "uint",
                    "description": "Selected temperature unit",
                },
            ],
        },
    }
    template = default_template_csv.default_template()
    result = render_csv.render_file(definitions, template, Path("docs.csv"))
    expected = """category,qualified_name,display_name,description,data_type,size_bytes,details\nfile,docs.csv,Command API docs,Auto generated docs,metadata,,\nstructure,cmd_temperature_set,Request temperature change,Request a change in temperature,structure,3,members=2\nstructure_member,cmd_temperature_set.temperature,temperature,Desired temperature,int,2,\nstructure_member,cmd_temperature_set.units,units,Selected temperature unit,uint,1,\n"""
    assert result == expected


def test_render_enum_rows() -> None:
    definitions = {
        "file": {
            "brief": "Command API docs",
            "description": "Auto generated docs",
        },
        "temperature_units": {
            "description": "The temperature units",
            "display_name": "Temperature units",
            "size": 1,
            "type": "enum",
            "values": [
                {
                    "label": "c",
                    "value": 0,
                    "display_name": "C",
                    "description": "Degrees Celsius",
                },
                {
                    "label": "f",
                    "display_name": "F",
                    "description": "Degrees Fahrenheit",
                },
            ],
        },
    }
    template = default_template_csv.default_template()
    result = render_csv.render_file(definitions, template, Path("docs.csv"))
    expected = """category,qualified_name,display_name,description,data_type,size_bytes,details\nfile,docs.csv,Command API docs,Auto generated docs,metadata,,\nenum,temperature_units,Temperature units,The temperature units,enum,1,values=2\nenum_value,temperature_units.c,C,Degrees Celsius,value,,value=0x0\nenum_value,temperature_units.f,F,Degrees Fahrenheit,value,,value=0x1\n"""
    assert result == expected
