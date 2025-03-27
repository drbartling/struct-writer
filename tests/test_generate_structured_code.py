from pathlib import Path

from struct_writer import default_template, generate_structured_code
from struct_writer.generate_structured_code import load_markup_file


def test_render_empty_file():
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_file(
        definitions, template, Path("my_file.h")
    )
    expected = """\
/**
* @file
* @brief A brief file description
*
* Longer prose describing what to find in the file
*
* @note This file is auto-generated using struct-writer
*/
#ifndef MY_FILE_H_
#define MY_FILE_H_
#ifdef __cplusplus
extern "C" {
#endif

#include <static_assert.h>
#include <stdint.h>

#ifdef __cplusplus
}
#endif
#endif // MY_FILE_H_
"""
    assert expected == result


def test_render_file_with_enum():
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
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
    template = default_template.default_template()
    result = generate_structured_code.render_file(
        definitions, template, Path("my_file.h")
    )
    expected = """\
/**
* @file
* @brief A brief file description
*
* Longer prose describing what to find in the file
*
* @note This file is auto-generated using struct-writer
*/
#ifndef MY_FILE_H_
#define MY_FILE_H_
#ifdef __cplusplus
extern "C" {
#endif

#include <static_assert.h>
#include <stdint.h>

/// Temperature units
/// The temperature units
typedef enum temperature_units_e{
/// Degrees Celsius
temperature_units_c = 0x0,
/// Degrees Fahrenheit
temperature_units_f,
} temperature_units_t;
STATIC_ASSERT_TYPE_SIZE(temperature_units_t, 1);

#ifdef __cplusplus
}
#endif
#endif // MY_FILE_H_
"""
    assert expected == result


def test_render_file_with_structure():
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
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
    template = default_template.default_template()
    result = generate_structured_code.render_file(
        definitions, template, Path("my_file.h")
    )
    expected = """\
/**
* @file
* @brief A brief file description
*
* Longer prose describing what to find in the file
*
* @note This file is auto-generated using struct-writer
*/
#ifndef MY_FILE_H_
#define MY_FILE_H_
#ifdef __cplusplus
extern "C" {
#endif

#include <static_assert.h>
#include <stdint.h>

/// Request temperature change
/// Request a change in temperature
typedef struct cmd_temperature_set_s{
/// Desired temperature
int16_t temperature;
/// Selected temperature unit
uint8_t units;
} cmd_temperature_set_t;
STATIC_ASSERT_TYPE_SIZE(cmd_temperature_set_t, 3);

#ifdef __cplusplus
}
#endif
#endif // MY_FILE_H_
"""
    assert expected == result


def test_render_empty_group():
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
        "my_commands": {
            "description": "A set of commands to do stuff",
            "display_name": "Command stuff",
            "type": "group",
            "size": 1,
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_file(
        definitions, template, Path("my_file.h")
    )
    expected = """\
/**
* @file
* @brief A brief file description
*
* Longer prose describing what to find in the file
*
* @note This file is auto-generated using struct-writer
*/
#ifndef MY_FILE_H_
#define MY_FILE_H_
#ifdef __cplusplus
extern "C" {
#endif

#include <static_assert.h>
#include <stdint.h>

#ifdef __cplusplus
}
#endif
#endif // MY_FILE_H_
"""
    assert expected == result


def test_render_file_from_example():
    definitions = load_markup_file(Path("examples/structures.toml"))
    template = default_template.default_template()
    result = generate_structured_code.render_file(
        definitions, template, Path("my_file.h")
    )
    expected = """\
/**
* @file
* @brief Command set for a thermostat
*
* Provides basic debug commands for a thermostat.  Allows for both imperial and metric units.
*
* @note This file is auto-generated using struct-writer
*/
#ifndef MY_FILE_H_
#define MY_FILE_H_
#ifdef __cplusplus
extern "C" {
#endif

#include <static_assert.h>
#include <stdint.h>

/// commands tag
/// Enumeration for commands tag
typedef enum commands_tag_e{
/// @see cmd_reset_t
commands_tag_reset = 0x1,
/// @see cmd_temperature_set_t
commands_tag_temperature_set = 0x2,
} commands_tag_t;
STATIC_ASSERT_TYPE_SIZE(commands_tag_t, 2);

/// reset request
/// Request a software reset
typedef struct cmd_reset_s{
/// Structure is intentionally empty (zero sized)
uint8_t empty[0];
} cmd_reset_t;
STATIC_ASSERT_TYPE_SIZE(cmd_reset_t, 0);

/// Thermostat command
/// Debug commands for thermostat
typedef struct commands_s{
/// commands tag
commands_tag_t tag;
union {
/// Request a software reset
cmd_reset_t reset;
/// Request a change in temperature
cmd_temperature_set_t temperature_set;
} value;
} commands_t;
STATIC_ASSERT_TYPE_SIZE(commands_t, 5);

/// HVAC State
/// State flags for HVAC
typedef struct hvac_state_s{
/// Set to true when fan is enabled
bool_t fan_enabled:1;
uint8_t reserved_1:1;
/// Set to true when air conditioning is enabled
bool_t ac_enabled:1;
/// Set to true when heater is enabled
bool_t heat_enabled:1;
/// Units used in thermostat
temperature_units_t units:1;
} hvac_state_t;
STATIC_ASSERT_TYPE_SIZE(hvac_state_t, 1);

#ifdef __cplusplus
}
#endif
#endif // MY_FILE_H_
"""
    assert expected == result
