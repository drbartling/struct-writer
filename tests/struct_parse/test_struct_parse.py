import logging
import struct
from typing import Any

import pytest

from struct_writer import struct_parse

logging.getLogger().setLevel(logging.DEBUG)


def example_definitions() -> dict[str, Any]:
    return {
        "file": {
            "brief": "Command set for a thermostat",
            "description": "Provides basic debug commands for a thermostat.  Allows for both imperial and metric units.",
        },
        "commands": {
            "description": "Debug commands for thermostat",
            "display_name": "Thermostat command",
            "type": "group",
            "size": 1,
        },
        "cmd_reset": {
            "description": "Request a software reset",
            "display_name": "reset request",
            "size": 0,
            "type": "structure",
            "groups": {
                "commands": {
                    "value": 1,
                    "name": "reset",
                },
            },
        },
        "cmd_temperature_set": {
            "description": "Request a change in temperature",
            "display_name": "Request temperature change",
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
                    "type": "temperature_units",
                    "description": "Selected temperature unit",
                },
            ],
            "size": 3,
            "type": "structure",
            "groups": {
                "commands": {
                    "value": 2,
                    "name": "temperature_set",
                },
            },
        },
        "temperature_units": {
            "description": "Units used for temperature",
            "display_name": "Temperature Units",
            "size": 1,
            "type": "enum",
            "values": [
                {
                    "label": "c",
                    "value": 0,
                    "display_name": "C",
                    "description": "Degrees Celcius",
                },
                {
                    "label": "f",
                    "display_name": "F",
                    "description": "Degrees Fahrenheit",
                },
            ],
        },
        "cmd_label_thermostat": {
            "description": "Give the thermostat a name",
            "display_name": "Label thermostat",
            "members": [
                {
                    "name": "label",
                    "size": 20,
                    "type": "str",
                    "description": "Name for the thermostat",
                },
            ],
            "size": 20,
            "type": "structure",
            "groups": {
                "commands": {
                    "value": 3,
                    "name": "label",
                },
            },
        },
        "cmd_mode_set": {
            "description": "Change thermostat mode",
            "display_name": "Request a change in the thermostat mode",
            "members": [
                {
                    "name": "mode",
                    "size": 1,
                    "type": "thermostat_mode",
                    "description": "Desired thermostat mode",
                },
            ],
            "size": 1,
            "type": "structure",
            "groups": {
                "commands": {
                    "value": 4,
                    "name": "mode_configuration",
                },
            },
        },
        "thermostat_mode": {
            "display_name": "Thermostat Mode",
            "description": "Mode configuration for thermostat control",
            "type": "bit_field",
            "size": 1,
            "members": [
                {
                    "name": "heating_en",
                    "start": 0,
                    "type": "uint",
                    "description": "Heating is enabled",
                },
                {
                    "name": "cooling_en",
                    "start": 1,
                    "type": "uint",
                    "description": "Cooling is enabled",
                },
                {
                    "name": "fan_always_on",
                    "start": 2,
                    "type": "fan_state",
                    "description": "Fan is always on",
                },
            ],
        },
        "fan_state": {
            "description": "Indicates how the fan should be operated",
            "display_name": "Fan state",
            "size": 1,
            "type": "enum",
            "values": [
                {
                    "label": "on_during_operation",
                    "display_name": "On during operation",
                    "description": "Fan is only on when actively heating or cooling",
                },
                {
                    "label": "always_on",
                    "display_name": "Always On",
                    "description": "Fan is always on, even when heater or A/C are not engaged",
                },
            ],
        },
    }


element_into_bytes_params = [
    ({"commands": {"cmd_reset": {}}}, (b"\x01")),
    (
        {
            "commands": {
                "cmd_temperature_set": {
                    "temperature": 75,
                    "units": "f",
                }
            }
        },
        (
            b"\x02"
            + (75).to_bytes(length=2, byteorder="big", signed=True)
            + b"\x01"
        ),
    ),
    (
        {
            "commands": {
                "cmd_label_thermostat": {
                    "label": "Living Room",
                }
            }
        },
        (b"\x03" + b"Living Room" + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
    ),
    (
        {
            "commands": {
                "cmd_label_thermostat": {
                    "label": "A very long room name that doesn't fit",
                }
            }
        },
        (b"\x03" + b"A very long room nam"),
    ),
    (
        {
            "commands": {
                "cmd_mode_set": {
                    "mode": {
                        "heating_en": 0,
                        "cooling_en": 1,
                        "fan_always_on": "always_on",
                    }
                }
            }
        },
        (b"\x04\x06"),
    ),
]


@pytest.mark.parametrize(("command", "expected"), element_into_bytes_params)
def test_element_into_bytes(command: dict[str, Any], expected: bytes) -> None:
    definitions = example_definitions()
    result = struct_parse.element_into_bytes(
        command, definitions, endianness="big"
    )
    assert expected == result


parse_bytes_params = [
    ((b""), "cmd_reset", {}),
    (b"\x00", "temperature_units", "c"),
    (b"\x01", "temperature_units", "f"),
    (b"\x00\x4b\x01", "cmd_temperature_set", {"temperature": 75, "units": "f"}),
    (
        b"\x02\x00\x4b\x01",
        "commands",
        {"cmd_temperature_set": {"temperature": 75, "units": "f"}},
    ),
    (
        b"\x06",
        "thermostat_mode",
        {"heating_en": 0, "cooling_en": 1, "fan_always_on": "always_on"},
    ),
]


@pytest.mark.parametrize(
    ("byte_data", "type_name", "expected"), parse_bytes_params
)
def test_parse_bytes(
    byte_data: bytes, type_name: str, expected: dict[str, Any]
) -> None:
    definitions = example_definitions()
    result = struct_parse.parse_bytes(byte_data, type_name, definitions)
    assert expected == result


def test_parse_bit_field_enums() -> None:
    definitions = {
        "a_bit_field": {
            "display_name": "",
            "description": "",
            "type": "bit_field",
            "size": 2,
            "members": [
                {
                    "name": "1",
                    "start": 0,
                    "bits": 4,
                    "type": "an_enum",
                    "description": "",
                },
                {
                    "name": "2",
                    "start": 4,
                    "bits": 4,
                    "type": "an_enum",
                    "description": "",
                },
                {
                    "name": "3",
                    "start": 8,
                    "bits": 4,
                    "type": "an_enum",
                    "description": "",
                },
                {
                    "name": "4",
                    "start": 12,
                    "bits": 4,
                    "type": "an_enum",
                    "description": "",
                },
            ],
        },
        "an_enum": {
            "display_name": "",
            "description": "",
            "type": "enum",
            "size": 1,
            "signed": True,
            "values": [
                {
                    "label": "a",
                    "value": -1,
                    "display_name": "",
                    "description": "",
                },
                {"label": "b", "display_name": "", "description": ""},
                {"label": "c", "display_name": "", "description": ""},
                {"label": "d", "display_name": "", "description": ""},
                {"label": "e", "display_name": "", "description": ""},
                {"label": "f", "display_name": "", "description": ""},
            ],
        },
    }
    data = {
        "a_bit_field": {
            "1": "a",
            "2": "b",
            "3": "c",
            "4": "d",
        }
    }
    byte_data = struct_parse.element_into_bytes(data, definitions)
    result = struct_parse.parse_bytes(byte_data, "a_bit_field", definitions)
    expected = {
        "1": "a",
        "2": "b",
        "3": "c",
        "4": "d",
    }
    assert expected == result


def test_oversized_bits_raise_exception() -> None:
    definitions = {
        "a_bit_field": {
            "display_name": "",
            "description": "",
            "type": "bit_field",
            "size": 1,
            "members": [
                {
                    "name": "1",
                    "start": 0,
                    "bits": 4,
                    "type": "int",
                    "description": "",
                },
                {
                    "name": "2",
                    "start": 4,
                    "bits": 4,
                    "type": "int",
                    "description": "",
                },
                {
                    "name": "3",
                    "start": 8,
                    "bits": 4,
                    "type": "int",
                    "description": "",
                },
                {
                    "name": "4",
                    "start": 12,
                    "bits": 4,
                    "type": "int",
                    "description": "",
                },
            ],
        },
    }
    byte_data = b"\x5a"

    result = struct_parse.parse_bytes(byte_data, "a_bit_field", definitions)
    expected = "5A (len=1)"
    assert result == expected


def test_offset_discriminator_in_group() -> None:
    """
    In most cases we want the tag in a group to be the first n bytes encountered
    in the stream. so in the byte stream: b'\x00\x0a\x0b\x0c' the first byte
    (b'\x00') would be the tag for the tagged union (or discriminator for
    discriminated type).  https://en.wikipedia.org/wiki/Tagged_union

    However some structures might be defined in a way that this doesn't work. In
    these cases where we need to maintain backwards compatibility with types
    defined where the tag is embedded within the stream, we can define an
    offset.  So if we set the offset to 2, then the third byte (zero indexed 2)
    would be the tag (b'\x0b')
    """

    definitions = {
        "my_tagged_union": {
            "display_name": "Tagged Union",
            "description": "Simple Tagged Union",
            "type": "group",
            "size": 1,
        },
        "unsigned_num": {
            "display_name": "Unsigned Number",
            "description": "A 7 byte Unsigned Number",
            "type": "structure",
            "size": 7,
            "members": [
                {
                    "name": "value_1",
                    "size": 3,
                    "type": "uint",
                    "description": "7 byte Unsigned Number",
                },
                {
                    "name": "value_2",
                    "size": 4,
                    "type": "uint",
                    "description": "7 byte Unsigned Number",
                },
            ],
            "groups": {"my_tagged_union": {"value": 0x00, "name": "unsigned"}},
        },
        "signed_num": {
            "display_name": "Signed Number",
            "description": "A 7 byte Signed Number",
            "type": "structure",
            "size": 7,
            "members": [
                {
                    "name": "value_1",
                    "size": 3,
                    "type": "int",
                    "description": "7 byte Signed Number",
                },
                {
                    "name": "value_2",
                    "size": 4,
                    "type": "int",
                    "description": "7 byte Signed Number",
                },
            ],
            "groups": {"my_tagged_union": {"value": 0x01, "name": "signed"}},
        },
    }

    # These shows the normal and preferred case
    byte_data = struct.pack(">II", 0x01FF_FFFF, 0xFFFF_FFFF)
    assert byte_data == b"\x01\xff\xff\xff\xff\xff\xff\xff"
    result = struct_parse.parse_bytes(byte_data, "my_tagged_union", definitions)
    expected = {"signed_num": {"value_1": -1, "value_2": -1}}
    assert result == expected

    byte_data = struct.pack(">II", 0x00FF_FFFF, 0xFFFF_FFFF)
    assert byte_data == b"\x00\xff\xff\xff\xff\xff\xff\xff"
    result = struct_parse.parse_bytes(byte_data, "my_tagged_union", definitions)
    expected = {"unsigned_num": {"value_1": 16777215, "value_2": 4294967295}}
    assert result == expected

    # While this shows the case where the tag is embedded in the middle of the
    # struct
    definitions["my_tagged_union"]["offset"] = 3
    byte_data = struct.pack("<II", 0x01FF_FFFF, 0xFFFF_FFFF)
    assert byte_data == b"\xff\xff\xff\x01\xff\xff\xff\xff"
    with pytest.deprecated_call():
        # The first time any group is parsed, a warning will be emitted
        result = struct_parse.parse_bytes(
            byte_data, "my_tagged_union", definitions
        )
    expected = {"signed_num": {"value_1": -1, "value_2": -1}}
    assert result == expected

    byte_data = struct.pack("<II", 0x00FF_FFFF, 0xFFFF_FFFF)
    assert byte_data == b"\xff\xff\xff\x00\xff\xff\xff\xff"
    # Subsequent attempts to parse the same struct will not emit a warning.
    result = struct_parse.parse_bytes(byte_data, "my_tagged_union", definitions)
    expected = {"unsigned_num": {"value_1": 16777215, "value_2": 4294967295}}
    assert result == expected

    byte_data = struct.pack("<II", 0x0012_34_56, 0x789A_BCDE)
    assert byte_data == b"\x56\x34\x12\x00\xde\xbc\x9a\x78"
    result = struct_parse.parse_bytes(
        byte_data, "my_tagged_union", definitions, endianness="little"
    )
    expected = {"unsigned_num": {"value_1": 0x12_3456, "value_2": 0x789A_BCDE}}
    assert result == expected
