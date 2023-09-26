import tomllib

from struct_writer import struct_parse


def test_enum_to_bytes():
    definitions = {
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
        "commands": {
            "description": "Debug commands for thermostat",
            "display_name": "Thermostat command",
            "type": "group",
        },
        "file": {
            "brief": "Command set for a thermostat",
            "description": "Provides basic debug commands for a thermostat.  Allows for both imperial and metric units.",
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
    }
    command = {
        "commands": {
            "cmd_temperature_set": {
                "temperature": 75,
                "units": "f",
            }
        }
    }
    result = struct_parse.struct_into_bytes(
        definitions, command, endianess="big"
    )
    expected = (
        b"\x02"
        + int(75).to_bytes(length=2, byteorder="big", signed=True)
        + b"\x01"
    )
    assert expected == result
