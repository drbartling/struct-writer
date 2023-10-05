import pytest

from struct_writer import struct_parse


def example_definitions():
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
                    "type": "int",
                    "description": "Heating is enabled",
                },
                {
                    "name": "cooling_en",
                    "start": 1,
                    "type": "int",
                    "description": "Cooling is enabled",
                },
                {
                    "name": "fan_always_on",
                    "start": 2,
                    "type": "int",
                    "description": "Fan is always on",
                },
            ],
        },
    }


struct_into_bytes_params = [
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
            + int(75).to_bytes(length=2, byteorder="big", signed=True)
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
        (
            b"\x03"
            + "Living Room".encode("utf-8")
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ),
    ),
    (
        {
            "commands": {
                "cmd_label_thermostat": {
                    "label": "A very long room name that doesn't fit",
                }
            }
        },
        (b"\x03" + "A very long room nam".encode("utf-8")),
    ),
    (
        {
            "commands": {
                "cmd_mode_set": {
                    "mode": {
                        "heating_en": 0,
                        "cooling_en": 1,
                        "fan_always_on": 1,
                    }
                }
            }
        },
        (b"\x04\x06"),
    ),
]


@pytest.mark.parametrize("command, expected", struct_into_bytes_params)
def test_element_into_bytes(command, expected):
    definitions = example_definitions()
    result = struct_parse.element_into_bytes(
        command, definitions, endianness="big"
    )
    assert expected == result


struct_into_bytes_params = [
    ((b""), "cmd_reset", {}),
    (b"\x00", "temperature_units", "c"),
    (b"\x01", "temperature_units", "f"),
    (b"\x00\x4B\x01", "cmd_temperature_set", {"temperature": 75, "units": "f"}),
    (
        b"\x02\x00\x4B\x01",
        "commands",
        {"cmd_temperature_set": {"temperature": 75, "units": "f"}},
    ),
]


@pytest.mark.parametrize(
    "byte_data,type_name, expected", struct_into_bytes_params
)
def test_parse_bytes(byte_data, type_name, expected):
    definitions = example_definitions()
    result = struct_parse.parse_bytes(byte_data, type_name, definitions)
    assert expected == result
