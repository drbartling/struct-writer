from pathlib import Path

from struct_writer import default_template_rust, render_rust


def test_render_empty_file():
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
    }
    template = default_template_rust.default_template()
    result = render_rust.render_file(definitions, template, Path("my_file.h"))
    expected = """\
/**
* @file
* @brief A brief file description
*
* Longer prose describing what to find in the file
*
* @note This file is auto-generated using struct-writer
*/
pub use my_file::*;
mod my_file {
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(dead_code)]

use modular_bitfield::prelude::*;
use zerocopy::*;

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

}
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
    template = default_template_rust.default_template()
    result = render_rust.render_file(definitions, template, Path("my_file.h"))
    expected = """\
/**
* @file
* @brief A brief file description
*
* Longer prose describing what to find in the file
*
* @note This file is auto-generated using struct-writer
*/
pub use my_file::*;
mod my_file {
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(dead_code)]

use modular_bitfield::prelude::*;
use zerocopy::*;

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

pub type temperature_units_slice = [u8;  1];
// Temperature units
// The temperature units
#[repr(u8)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Default, Debug, Clone, PartialEq, Eq, Hash, Immutable, KnownLayout, IntoBytes, TryFromBytes, BitfieldSpecifier,
)]
#[bits = 1]
pub enum temperature_units {
#[default]
/// Degrees Celsius
c = 0x0,
/// Degrees Fahrenheit
f = 0x1,
}
const TEMPERATURE_UNITS_SIZE_ASSERT: [u8; 1] = [0; std::mem::size_of::<temperature_units>()];

impl From<temperature_units> for temperature_units_slice {
fn from(value: temperature_units) -> Self {
transmute!(value)
}
}

}
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
    template = default_template_rust.default_template()
    result = render_rust.render_file(definitions, template, Path("my_file.h"))
    expected = """\
/**
* @file
* @brief A brief file description
*
* Longer prose describing what to find in the file
*
* @note This file is auto-generated using struct-writer
*/
pub use my_file::*;
mod my_file {
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(dead_code)]

use modular_bitfield::prelude::*;
use zerocopy::*;

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

pub type cmd_temperature_set_slice = [u8;  3];
// Request temperature change
// Request a change in temperature
#[repr(packed)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Default, Debug, Clone, PartialEq, Eq, Hash, Immutable, KnownLayout, IntoBytes, TryFromBytes,
)]
pub struct cmd_temperature_set{
/// Desired temperature
temperature: i16,
/// Selected temperature unit
units: u8,
}
const CMD_TEMPERATURE_SET_SIZE_ASSERT: [u8; 3] = [0; std::mem::size_of::<cmd_temperature_set>()];

}
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
    template = default_template_rust.default_template()
    result = render_rust.render_file(definitions, template, Path("my_file.h"))
    expected = """\
/**
* @file
* @brief A brief file description
*
* Longer prose describing what to find in the file
*
* @note This file is auto-generated using struct-writer
*/
pub use my_file::*;
mod my_file {
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(dead_code)]

use modular_bitfield::prelude::*;
use zerocopy::*;

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

}
"""
    assert expected == result


def test_render_small_group():
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
        "commands": {
            "description": "Debug commands for thermostat",
            "display_name": "Thermostat command",
            "type": "group",
            "size": 2,
        },
        "cmd_reset": {
            "description": "Request a software reset",
            "display_name": "Reset Request",
            "type": "structure",
            "size": 0,
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
            "type": "structure",
            "size": 3,
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
            "groups": {
                "commands": {
                    "value": 2,
                    "name": "temperature_set",
                },
            },
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
    template = default_template_rust.default_template()
    result = render_rust.render_file(definitions, template, Path("my_file.h"))
    expected = """\
/**
* @file
* @brief A brief file description
*
* Longer prose describing what to find in the file
*
* @note This file is auto-generated using struct-writer
*/
pub use my_file::*;
mod my_file {
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(dead_code)]

use modular_bitfield::prelude::*;
use zerocopy::*;

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

pub type commands_slice = [u8;  6];
#[repr(u16)]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Immutable, KnownLayout, IntoBytes, TryFromBytes,)]
pub enum commands {
reset(cmd_reset, [u8;4]) = 1,
temperature_set(cmd_temperature_set, [u8;1]) = 2,
}
const COMMANDS_SIZE_ASSERT: [u8; 6] = [0; std::mem::size_of::<commands>()];

impl From<commands> for commands_slice {
    fn from(value: commands) -> Self {
        transmute!(value)
    }
}

impl TryFrom<&[u8]> for commands {
    type Error = ();

    fn try_from(value: &[u8]) -> Result<Self, Self::Error> {
        let r = commands::try_ref_from_bytes(value).map_err(|_| ())?;
        Ok(r.to_owned())
    }
}

impl TryFrom<commands_slice> for commands {
    type Error = ValidityError<commands_slice, commands>;

    fn try_from(value: commands_slice) -> Result<Self, Self::Error> {
        try_transmute!(value)
    }
}
pub type cmd_reset_slice = [u8;  0];
// Reset Request
// Request a software reset
#[repr(packed)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Default, Debug, Clone, PartialEq, Eq, Hash, Immutable, KnownLayout, IntoBytes, TryFromBytes,
)]
pub struct cmd_reset{
// Structure is intentionally empty (zero sized)
}
const CMD_RESET_SIZE_ASSERT: [u8; 0] = [0; std::mem::size_of::<cmd_reset>()];

pub type temperature_units_slice = [u8;  1];
// Temperature units
// The temperature units
#[repr(u8)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Default, Debug, Clone, PartialEq, Eq, Hash, Immutable, KnownLayout, IntoBytes, TryFromBytes, BitfieldSpecifier,
)]
#[bits = 1]
pub enum temperature_units {
#[default]
/// Degrees Celsius
c = 0x0,
/// Degrees Fahrenheit
f = 0x1,
}
const TEMPERATURE_UNITS_SIZE_ASSERT: [u8; 1] = [0; std::mem::size_of::<temperature_units>()];

impl From<temperature_units> for temperature_units_slice {
fn from(value: temperature_units) -> Self {
transmute!(value)
}
}

pub type cmd_temperature_set_slice = [u8;  3];
// Request temperature change
// Request a change in temperature
#[repr(packed)]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Default, Debug, Clone, PartialEq, Eq, Hash, Immutable, KnownLayout, IntoBytes, TryFromBytes,
)]
pub struct cmd_temperature_set{
/// Desired temperature
temperature: i16,
/// Selected temperature unit
units: [u8; 1],
}
const CMD_TEMPERATURE_SET_SIZE_ASSERT: [u8; 3] = [0; std::mem::size_of::<cmd_temperature_set>()];

}
"""
    print(result)
    assert expected == result


def test_render_bitfield():
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
        "cmd_temperature_set": {
            "description": "Request a change in temperature",
            "display_name": "Request temperature change",
            "size": 2,
            "type": "bit_field",
            "members": [
                {
                    "name": "temperature",
                    "start": 0,
                    "bits": 8,
                    "type": "int",
                    "description": "Desired temperature",
                },
                {
                    "name": "units",
                    "start": 9,
                    "bits": 2,
                    "type": "uint",
                    "description": "Selected temperature unit",
                },
            ],
        },
    }
    template = default_template_rust.default_template()
    result = render_rust.render_file(definitions, template, Path("my_file.h"))
    expected = """\
/**
* @file
* @brief A brief file description
*
* Longer prose describing what to find in the file
*
* @note This file is auto-generated using struct-writer
*/
pub use my_file::*;
mod my_file {
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(dead_code)]

use modular_bitfield::prelude::*;
use zerocopy::*;

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

pub type cmd_temperature_set_slice = [u8;  2];
// Request temperature change
// Request a change in temperature
#[repr(u16)]
#[bitfield]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Default, Debug, Clone, PartialEq, Eq, Hash, Immutable, KnownLayout, IntoBytes, TryFromBytes,
)]
pub struct cmd_temperature_set{
/// Desired temperature
pub temperature: int,
#[skip]
reserved_8: B1,
/// Selected temperature unit
pub units: uint,
#[skip]
reserved_11: B5,
}
const CMD_TEMPERATURE_SET_SIZE_ASSERT: [u8; 2] = [0; std::mem::size_of::<cmd_temperature_set>()];

}
"""
    print(result)
    assert expected == result
