from pathlib import Path

from struct_writer import default_template, generate_structured_code
from struct_writer.generate_structured_code import load_markup_file


def test_render_enum():
    definitions = {
        "MY_enum": {
            "type": "enum",
            "display_name": "My enum",
            "description": "An enum",
            "size": 1,
            "values": [
                {
                    "value": 0,
                    "label": "first_value",
                    "description": "The first value in this enum",
                },
                {
                    "label": "second_value",
                    "description": "The second value in this enum",
                },
            ],
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// My enum
/// An enum
typedef enum MY_enum_e{
/// The first value in this enum
MY_enum_first_value = 0x0,
/// The second value in this enum
MY_enum_second_value,
} MY_enum_t;
STATIC_ASSERT_TYPE_SIZE(MY_enum_t, 1);

"""

    assert expected == result


def test_render_empty_struct():
    definitions = {
        "MY_empty_struct": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 0,
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// My struct
/// A struct
typedef struct MY_empty_struct_s{
/// Structure is intentionally empty (zero sized)
uint8_t empty[0];
} MY_empty_struct_t;
STATIC_ASSERT_TYPE_SIZE(MY_empty_struct_t, 0);

"""

    assert expected == result


def test_render_struct():
    definitions = {
        "MY_struct": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 1,
            "members": [
                {
                    "name": "foo",
                    "size": 1,
                    "type": "int",
                    "description": "A foo walks into a bar",
                },
            ],
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// My struct
/// A struct
typedef struct MY_struct_s{
/// A foo walks into a bar
int8_t foo;
} MY_struct_t;
STATIC_ASSERT_TYPE_SIZE(MY_struct_t, 1);

"""

    assert expected == result


def test_render_empty_group():
    definitions = {
        "MY_empty_group": {
            "type": "group",
            "display_name": "My group",
            "description": "A group",
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = ""

    assert expected == result


def test_render_group():
    definitions = {
        "MY_group": {
            "type": "group",
            "display_name": "My group",
            "description": "A group",
            "size": 1,
        },
        "MY_grouped_struct": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 0,
            "groups": {
                "MY_group": {"value": 0, "name": "grouped_struct"},
            },
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// MY_group tag
/// Enumeration for MY_group tag
typedef enum MY_group_tag_e{
/// @see MY_grouped_struct_t
MY_group_tag_grouped_struct = 0x0,
} MY_group_tag_t;
STATIC_ASSERT_TYPE_SIZE(MY_group_tag_t, 1);

/// My struct
/// A struct
typedef struct MY_grouped_struct_s{
/// Structure is intentionally empty (zero sized)
uint8_t empty[0];
} MY_grouped_struct_t;
STATIC_ASSERT_TYPE_SIZE(MY_grouped_struct_t, 0);

/// My group
/// A group
typedef struct MY_group_s{
/// MY_group tag
MY_group_tag_t tag;
union {
/// A struct
MY_grouped_struct_t grouped_struct;
} value;
} MY_group_t;
STATIC_ASSERT_TYPE_SIZE(MY_group_t, 1);

"""

    assert expected == result


def test_render_structs_in_dependency_order():
    definitions = {
        "MY_struct1": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 1,
            "members": [
                {
                    "name": "foo",
                    "size": 1,
                    "type": "MY_struct2",
                    "description": "A foo walks into a bar",
                },
            ],
        },
        "MY_struct2": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 1,
            "members": [
                {
                    "name": "bar",
                    "size": 1,
                    "type": "int",
                    "description": "A bar",
                },
            ],
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// My struct
/// A struct
typedef struct MY_struct2_s{
/// A bar
int8_t bar;
} MY_struct2_t;
STATIC_ASSERT_TYPE_SIZE(MY_struct2_t, 1);

/// My struct
/// A struct
typedef struct MY_struct1_s{
/// A foo walks into a bar
MY_struct2_t foo;
} MY_struct1_t;
STATIC_ASSERT_TYPE_SIZE(MY_struct1_t, 1);

"""

    assert expected == result


def test_render_bit_field():
    definitions = {
        "MY_field": {
            "type": "bit_field",
            "display_name": "My field",
            "description": "A bit field",
            "size": 1,
            "members": [
                {
                    "name": "foo",
                    "start": 1,
                    "last": 3,
                    "bits": 3,
                    "type": "int",
                    "description": "foo",
                },
                {
                    "name": "bar",
                    "start": 4,
                    "bits": 1,
                    "type": "uint",
                    "description": "bar",
                },
                {
                    "name": "baz",
                    "start": 6,
                    "type": "uint",
                    "description": "baz",
                },
                {
                    "name": "bazz",
                    "start": 7,
                    "last": 7,
                    "type": "uint",
                    "description": "bazz",
                },
            ],
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// My field
/// A bit field
typedef struct MY_field_s{
uint8_t reserved_0:1;
/// foo
int8_t foo:3;
/// bar
uint8_t bar:1;
uint8_t reserved_5:1;
/// baz
uint8_t baz:1;
/// bazz
uint8_t bazz:1;
} MY_field_t;
STATIC_ASSERT_TYPE_SIZE(MY_field_t, 1);

"""
    assert expected == result


def test_render_bit_field_with_enum():
    definitions = {
        "MY_field2": {
            "type": "bit_field",
            "display_name": "My field",
            "description": "A bit field",
            "size": 2,
            "members": [
                {
                    "name": "power",
                    "start": 2,
                    "bits": 1,
                    "type": "MY_power",
                    "description": "Power",
                }
            ],
        },
        "MY_power": {
            "type": "enum",
            "display_name": "Power",
            "description": "Power state",
            "size": 1,
            "values": [
                {
                    "value": 0,
                    "label": "off",
                    "description": "The power is off",
                },
                {
                    "value": 1,
                    "label": "on",
                    "description": "The power is on",
                },
            ],
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// Power
/// Power state
typedef enum MY_power_e{
/// The power is off
MY_power_off = 0x0,
/// The power is on
MY_power_on = 0x1,
} MY_power_t;
STATIC_ASSERT_TYPE_SIZE(MY_power_t, 1);

/// My field
/// A bit field
typedef struct MY_field2_s{
uint16_t reserved_0:2;
/// Power
MY_power_t power:1;
} MY_field2_t;
STATIC_ASSERT_TYPE_SIZE(MY_field2_t, 2);

"""
    assert expected == result


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

#ifdef __cplusplus
}
#endif
#endif // MY_FILE_H_
"""
    assert expected == result
