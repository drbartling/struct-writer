from pathlib import Path
from typing import Any

import pytest
from devtools import debug

from struct_writer.definitions import (
    BitField,
    BitFieldMember,
    Enumeration,
    EnumValue,
    FileDescription,
    Group,
    GroupMember,
    ParseFailed,
    Structure,
    StructureMember,
    TypeDefinitions,
)
from struct_writer.generate_structured_code import load_markup_file

structure_params = [
    (
        "Empty Structure",
        {
            "empty_struct": {
                "description": "An empty structure",
                "display_name": "Empty Structure",
                "size": 0,
            }
        },
        Structure(
            name="empty_struct",
            display_name="Empty Structure",
            description="An empty structure",
            size=0,
            members=[],
        ),
    ),
    (
        "Simple Structure",
        {
            "simple_struct": {
                "description": "A simple structure",
                "display_name": "Simple Structure",
                "size": 1,
                "members": [
                    {
                        "name": "number",
                        "size": 1,
                        "type": "int",
                        "description": "A small number",
                    },
                ],
            }
        },
        Structure(
            name="simple_struct",
            display_name="Simple Structure",
            description="A simple structure",
            size=1,
            members=[
                StructureMember(
                    name="number",
                    size=1,
                    type="int",
                    description="A small number",
                )
            ],
        ),
    ),
]


@pytest.mark.parametrize(
    ("test_name", "structure_dict", "expected"), structure_params
)
def test_structure(
    test_name: str, structure_dict: dict[str, Any], expected: Structure
) -> None:
    debug(test_name)
    result = Structure.from_dict(structure_dict)
    debug(result)
    debug(expected)
    assert expected == result


def test_mismatch_structure_size() -> None:
    struct = {
        "simple_struct": {
            "description": "A simple structure",
            "display_name": "Simple Structure",
            "size": 0,
            "type": "structure",
            "members": [
                {
                    "name": "number",
                    "size": 1,
                    "type": "int",
                    "description": "A small number",
                },
            ],
        }
    }
    with pytest.raises(ParseFailed):
        _ = Structure.from_dict(struct)


type_definitions_params = [
    (
        "Empty Structure",
        {
            "empty_struct": {
                "description": "An empty structure",
                "display_name": "Empty Structure",
                "type": "structure",
                "size": 0,
            }
        },
        TypeDefinitions(
            FileDescription.empty(),
            {
                "empty_struct": Structure(
                    name="empty_struct",
                    display_name="Empty Structure",
                    description="An empty structure",
                    size=0,
                    members=[],
                ),
            },
        ),
    ),
    (
        "Simple Structure",
        {
            "simple_struct": {
                "description": "A simple structure",
                "display_name": "Simple Structure",
                "type": "structure",
                "size": 1,
                "members": [
                    {
                        "name": "number",
                        "size": 1,
                        "type": "int",
                        "description": "A small number",
                    },
                ],
            }
        },
        TypeDefinitions(
            FileDescription.empty(),
            {
                "simple_struct": Structure(
                    name="simple_struct",
                    display_name="Simple Structure",
                    description="A simple structure",
                    size=1,
                    members=[
                        StructureMember(
                            name="number",
                            size=1,
                            type="int",
                            description="A small number",
                        )
                    ],
                )
            },
        ),
    ),
    (
        "Enum",
        {
            "an_enum": {
                "description": "an example enum",
                "display_name": "An Enum",
                "type": "enum",
                "size": 1,
                "values": [
                    {
                        "label": "a",
                        "value": 0,
                        "display_name": "A",
                        "description": "The letter A",
                    },
                    {
                        "label": "b",
                        "value": 1,
                        "display_name": "B",
                        "description": "The letter B",
                    },
                ],
            }
        },
        TypeDefinitions(
            FileDescription.empty(),
            {
                "an_enum": Enumeration(
                    name="an_enum",
                    description="an example enum",
                    display_name="An Enum",
                    size=1,
                    values=[
                        EnumValue(
                            label="a",
                            value=0,
                            display_name="A",
                            description="The letter A",
                        ),
                        EnumValue(
                            label="b",
                            value=1,
                            display_name="B",
                            description="The letter B",
                        ),
                    ],
                )
            },
        ),
    ),
    (
        "Empty Bit Field",
        {
            "a_bit_field": {
                "description": "An example bit field",
                "display_name": "A Bit Field",
                "type": "bit_field",
                "size": 0,
            },
        },
        TypeDefinitions(
            FileDescription.empty(),
            {
                "a_bit_field": BitField(
                    description="An example bit field",
                    display_name="A Bit Field",
                    members=[],
                    name="a_bit_field",
                    size=0,
                )
            },
        ),
    ),
    (
        "Simple Bit Field",
        {
            "a_bit_field": {
                "description": "An example bit field",
                "display_name": "A Bit Field",
                "type": "bit_field",
                "size": 1,
                "members": [
                    {
                        "name": "a_number",
                        "start": 0,
                        "end": 4,
                        "bits": 4,
                        "type": "uint",
                        "description": "A 4 bit number",
                    },
                    {
                        "name": "reserved_4",
                        "start": 4,
                        "end": 8,
                        "bits": 4,
                        "type": "reserved",
                        "description": "Unused bits",
                    },
                ],
            },
        },
        TypeDefinitions(
            FileDescription.empty(),
            {
                "a_bit_field": BitField(
                    description="An example bit field",
                    display_name="A Bit Field",
                    members=[
                        BitFieldMember(
                            name="a_number",
                            start=0,
                            end=4,
                            bits=4,
                            type="uint",
                            description="A 4 bit number",
                        ),
                        BitFieldMember(
                            name="reserved_4",
                            start=4,
                            end=8,
                            bits=4,
                            type="reserved",
                            description="Unused bits",
                        ),
                    ],
                    name="a_bit_field",
                    size=1,
                )
            },
        ),
    ),
    (
        "Grouped Structures",
        {
            "small_group": {
                "description": "A Small Example Group",
                "display_name": "Small Group",
                "type": "group",
                "size": 1,
            },
            "simple_struct": {
                "description": "A simple structure",
                "display_name": "Simple Structure",
                "type": "structure",
                "size": 1,
                "members": [
                    {
                        "name": "number",
                        "size": 1,
                        "type": "int",
                        "description": "A small number",
                    },
                ],
                "groups": {
                    "small_group": {"value": 1, "name": "simple"},
                },
            },
        },
        TypeDefinitions(
            FileDescription.empty(),
            {
                "small_group": Group(
                    name="small_group",
                    display_name="Small Group",
                    description="A Small Example Group",
                    size=1,
                    members=[
                        GroupMember(
                            name="simple", type="simple_struct", value=1
                        ),
                    ],
                ),
                "simple_struct": Structure(
                    name="simple_struct",
                    display_name="Simple Structure",
                    description="A simple structure",
                    size=1,
                    members=[
                        StructureMember(
                            name="number",
                            size=1,
                            type="int",
                            description="A small number",
                        )
                    ],
                ),
            },
        ),
    ),
]


@pytest.mark.parametrize(
    ("test_name", "definition_dict", "expected"), type_definitions_params
)
def test_type_definitions(
    test_name: str, definition_dict: dict[str, Any], expected: TypeDefinitions
) -> None:
    debug(test_name)
    result = TypeDefinitions.from_dict(definition_dict)
    debug(result)
    debug(expected)
    assert expected == result


def test_example_file() -> None:
    this_file = Path(__file__).absolute()
    tests_dir = this_file.parent
    project_dir = tests_dir.parent
    example_file = project_dir / "examples/structures.toml"
    definitions = load_markup_file(example_file)

    result = TypeDefinitions.from_dict(definitions)
    debug(result)

    expected = TypeDefinitions(
        FileDescription(
            "Command set for a thermostat",
            "Provides basic debug commands for a thermostat.  Allows for both imperial and metric units.",
        ),
        {
            "cmd_reset": Structure(
                description="Request a software reset",
                display_name="reset request",
                members=[],
                name="cmd_reset",
                size=0,
            ),
            "cmd_temperature_set": Structure(
                description="Request a change in temperature",
                display_name="Request temperature change",
                members=[
                    StructureMember(
                        description="Desired temperature",
                        name="temperature",
                        size=2,
                        type="int",
                    ),
                    StructureMember(
                        description="Selected temperature unit",
                        name="units",
                        size=1,
                        type="temperature_units",
                    ),
                    StructureMember(
                        description="reserved",
                        name="reserved",
                        size=1,
                        type="bool",
                    ),
                ],
                name="cmd_temperature_set",
                size=4,
            ),
            "commands": Group(
                name="commands",
                display_name="Thermostat command",
                description="Debug commands for thermostat",
                size=2,
                members=[
                    GroupMember(
                        name="reset",
                        type="cmd_reset",
                        value=1,
                    ),
                    GroupMember(
                        name="temperature_set",
                        type="cmd_temperature_set",
                        value=2,
                    ),
                ],
            ),
            "hvac_state": BitField(
                description="State flags for HVAC",
                display_name="HVAC State",
                size=1,
                name="hvac_state",
                members=[
                    BitFieldMember(
                        name="fan_enabled",
                        start=0,
                        end=1,
                        bits=1,
                        type="bool",
                        description="Set to true when fan is enabled",
                    ),
                    BitFieldMember(
                        name="reserved_1",
                        start=1,
                        end=2,
                        bits=1,
                        type="reserved",
                        description="Reserved",
                    ),
                    BitFieldMember(
                        name="ac_enabled",
                        start=2,
                        end=3,
                        bits=1,
                        type="bool",
                        description="Set to true when air conditioning is enabled",
                    ),
                    BitFieldMember(
                        name="heat_enabled",
                        start=3,
                        end=4,
                        bits=1,
                        type="bool",
                        description="Set to true when heater is enabled",
                    ),
                    BitFieldMember(
                        name="units",
                        start=4,
                        end=5,
                        bits=1,
                        type="temperature_units",
                        description="Units used in thermostat",
                    ),
                    BitFieldMember(
                        name="reserved_5",
                        start=5,
                        end=8,
                        bits=3,
                        type="reserved",
                        description="Reserved",
                    ),
                ],
            ),
            "temperature_units": Enumeration(
                name="temperature_units",
                values=[
                    EnumValue(
                        label="c",
                        value=0,
                        display_name="C",
                        description="Degrees Celsius",
                    ),
                    EnumValue(
                        label="f",
                        value=1,
                        display_name="F",
                        description="Degrees Fahrenheit",
                    ),
                ],
                description="Units used for temperature",
                display_name="Temperature Units",
                size=1,
            ),
        },
    )
    debug(expected)
    assert expected == result
