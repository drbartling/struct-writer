from pathlib import Path

from struct_writer import default_template_c, generate_structured_code, render_c


def test_default_template() -> None:
    # We want to ensure that the default template we use for c is the same
    # as the example we give in documentation

    this_path = Path(__file__).resolve()
    project_root = this_path / "../.."
    project_root = project_root.resolve()
    template_example = project_root / "examples/template_c.toml"
    assert template_example.is_file()

    example_template = generate_structured_code.load_markup_file(
        template_example
    )
    default_template = default_template_c.default_template()

    assert example_template == default_template


def test_render_empty_file() -> None:
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
    }
    template = default_template_c.default_template()
    result = render_c.render_file(definitions, template, Path("my_file.h"))
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


def test_render_file_with_enum() -> None:
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
    template = default_template_c.default_template()
    result = render_c.render_file(definitions, template, Path("my_file.h"))
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


def test_render_file_with_structure() -> None:
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
    template = default_template_c.default_template()
    result = render_c.render_file(definitions, template, Path("my_file.h"))
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


def test_render_empty_group() -> None:
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
    template = default_template_c.default_template()
    result = render_c.render_file(definitions, template, Path("my_file.h"))
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
