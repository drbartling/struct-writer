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

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

pub type temperature_units_slice = [u8;  1];
// Temperature units
// The temperature units
#[derive(
    Default, Debug, Clone, PartialEq, Copy,
)]#[derive(BitfieldSpecifier)]
#[bits = 1]

pub enum temperature_units {
#[default]
/// Degrees Celsius
c = 0x0,
/// Degrees Fahrenheit
f = 0x1,
}

impl From<temperature_units> for temperature_units_slice {
fn from(value: temperature_units) -> Self {
let v = value as u8;
v.to_le_bytes()
}
}

impl TryFrom<&[u8]> for temperature_units {
type Error = ();
fn try_from(value: &[u8]) -> Result<Self, ()> {
assert!(value.len() >= size_of::<temperature_units_slice>());
let v: temperature_units_slice = value[..size_of::<temperature_units_slice>()]
.try_into()
.map_err(|_| ())?;
Self::try_from(v)
}
}

impl TryFrom<temperature_units_slice> for temperature_units {
type Error = ();
fn try_from(value: temperature_units_slice) -> Result<Self, ()> {
let v = u8::from_le_bytes(value);
v.try_into()
}
}

impl TryFrom<u8> for temperature_units {
type Error = ();
fn try_from(value: u8) -> Result<Self, ()> {
match value {
0 => Ok(temperature_units::c),
1 => Ok(temperature_units::f),
_ => Err(()),
}
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

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

pub type cmd_temperature_set_slice = [u8;  3];
// Request temperature change
// Request a change in temperature
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Debug, Clone, PartialEq,
)]
pub struct cmd_temperature_set{
/// Desired temperature
pub temperature: i16,
/// Selected temperature unit
pub units: u8,
}

impl From<cmd_temperature_set> for cmd_temperature_set_slice {
#[allow(unused_variables)]
fn from(value: cmd_temperature_set) -> Self {
#[allow(unused_mut)]
let mut buf: cmd_temperature_set_slice = [0; 3];

buf[0..2].copy_from_slice(&value.temperature.to_le_bytes());
buf[2..3].copy_from_slice(&value.units.to_le_bytes());

buf
}
}

impl TryFrom<cmd_temperature_set_slice> for cmd_temperature_set {
type Error = ();
fn try_from(input: cmd_temperature_set_slice) -> Result<Self, ()> {
    let input: &[u8] = &input;
    input.try_into()
}
}

impl TryFrom<&[u8]> for cmd_temperature_set {
type Error = ();
fn try_from(input: &[u8]) -> Result<Self, ()> {
assert!(input.len() >= size_of::<cmd_temperature_set_slice>());

Ok(Self{
temperature: i16::from_le_bytes(input[0..2].try_into().unwrap()),
units: u8::from_le_bytes(input[2..3].try_into().unwrap()),
})

}
}

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

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

pub type commands_slice = [u8;  5];
// Thermostat command
// Debug commands for thermostat
#[repr(u16)]
#[derive(Debug, Clone, PartialEq, )]
pub enum commands {
reset(cmd_reset) = 1,
temperature_set(cmd_temperature_set) = 2,
}
impl commands {
pub fn size(&self) -> usize {
match self{
commands::reset(_) => 2,
commands::temperature_set(_) => 5,
}
}
pub fn size_from_tag(tag: u16) -> Option<usize> {
match tag {
0x01 => Some(2), // commands::reset
0x02 => Some(5), // commands::temperature_set
 _ => None,}
}
}
impl From<commands> for commands_slice {
fn from(value: commands) -> Self {
#[allow(unused_mut)]
let mut buf = [0_u8; 5];
match value {
commands::reset(inner) => {
buf[0..2].copy_from_slice(&1_u16.to_le_bytes());
let inner_buf: cmd_reset_slice = inner.into();
buf[2..2].copy_from_slice(&inner_buf);
}
commands::temperature_set(inner) => {
buf[0..2].copy_from_slice(&2_u16.to_le_bytes());
let inner_buf: cmd_temperature_set_slice = inner.into();
buf[2..5].copy_from_slice(&inner_buf);
}
}
buf
}
}
impl TryFrom<&[u8]> for commands {
type Error = ();

fn try_from(value: &[u8]) -> Result<Self, Self::Error> {
if !(value.len() >= 2) {return Err(());}
let repr_int = u16::from_le_bytes(value[0..2].try_into().unwrap());
match repr_int {
1 => {
let inner_buf: &[u8] = &value[2..];
let inner = inner_buf.try_into()?;
Ok(commands::reset(inner))
}
2 => {
let inner_buf: &[u8] = &value[2..];
let inner = inner_buf.try_into()?;
Ok(commands::temperature_set(inner))
}
_ => Err(()),
}
}
}

impl TryFrom<commands_slice> for commands {
type Error = ();

fn try_from(value: commands_slice) -> Result<Self, Self::Error> {
let r: &[u8] = &value;
r.try_into()
}
}
pub type cmd_reset_slice = [u8;  0];
// Reset Request
// Request a software reset
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Debug, Clone, PartialEq,
)]
pub struct cmd_reset{
// Structure is intentionally empty (zero sized)
}

impl From<cmd_reset> for cmd_reset_slice {
#[allow(unused_variables)]
fn from(value: cmd_reset) -> Self {
#[allow(unused_mut)]
let mut buf: cmd_reset_slice = [0; 0];



buf
}
}

impl TryFrom<cmd_reset_slice> for cmd_reset {
type Error = ();
fn try_from(input: cmd_reset_slice) -> Result<Self, ()> {
    let input: &[u8] = &input;
    input.try_into()
}
}

impl TryFrom<&[u8]> for cmd_reset {
type Error = ();
fn try_from(input: &[u8]) -> Result<Self, ()> {
assert!(input.len() >= size_of::<cmd_reset_slice>());

Ok(Self{

})

}
}

pub type temperature_units_slice = [u8;  1];
// Temperature units
// The temperature units
#[derive(
    Default, Debug, Clone, PartialEq, Copy,
)]#[derive(BitfieldSpecifier)]
#[bits = 1]

pub enum temperature_units {
#[default]
/// Degrees Celsius
c = 0x0,
/// Degrees Fahrenheit
f = 0x1,
}

impl From<temperature_units> for temperature_units_slice {
fn from(value: temperature_units) -> Self {
let v = value as u8;
v.to_le_bytes()
}
}

impl TryFrom<&[u8]> for temperature_units {
type Error = ();
fn try_from(value: &[u8]) -> Result<Self, ()> {
assert!(value.len() >= size_of::<temperature_units_slice>());
let v: temperature_units_slice = value[..size_of::<temperature_units_slice>()]
.try_into()
.map_err(|_| ())?;
Self::try_from(v)
}
}

impl TryFrom<temperature_units_slice> for temperature_units {
type Error = ();
fn try_from(value: temperature_units_slice) -> Result<Self, ()> {
let v = u8::from_le_bytes(value);
v.try_into()
}
}

impl TryFrom<u8> for temperature_units {
type Error = ();
fn try_from(value: u8) -> Result<Self, ()> {
match value {
0 => Ok(temperature_units::c),
1 => Ok(temperature_units::f),
_ => Err(()),
}
}
}

pub type cmd_temperature_set_slice = [u8;  3];
// Request temperature change
// Request a change in temperature
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Debug, Clone, PartialEq,
)]
pub struct cmd_temperature_set{
/// Desired temperature
pub temperature: i16,
/// Selected temperature unit
pub units: temperature_units,
}

impl From<cmd_temperature_set> for cmd_temperature_set_slice {
#[allow(unused_variables)]
fn from(value: cmd_temperature_set) -> Self {
#[allow(unused_mut)]
let mut buf: cmd_temperature_set_slice = [0; 3];

buf[0..2].copy_from_slice(&value.temperature.to_le_bytes());
let temp: [u8; 1] = value.units.into();
buf[2..3].copy_from_slice(&temp);


buf
}
}

impl TryFrom<cmd_temperature_set_slice> for cmd_temperature_set {
type Error = ();
fn try_from(input: cmd_temperature_set_slice) -> Result<Self, ()> {
    let input: &[u8] = &input;
    input.try_into()
}
}

impl TryFrom<&[u8]> for cmd_temperature_set {
type Error = ();
fn try_from(input: &[u8]) -> Result<Self, ()> {
assert!(input.len() >= size_of::<cmd_temperature_set_slice>());

Ok(Self{
temperature: i16::from_le_bytes(input[0..2].try_into().unwrap()),
units: input[2..3].try_into()?,
})

}
}

}
"""
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

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

pub type cmd_temperature_set_slice = [u8;  2];
// Request temperature change
// Request a change in temperature
#[bitfield]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Debug, Clone, PartialEq, Copy,
)]
pub struct cmd_temperature_set{
/// Desired temperature
pub temperature: int,
#[skip]
reserved_8: B1,
/// Selected temperature unit
pub units: B2,
#[skip]
reserved_11: B5,
}

impl From<cmd_temperature_set> for cmd_temperature_set_slice {
fn from(input: cmd_temperature_set) -> Self {
input.into_bytes()
}
}

impl TryFrom<cmd_temperature_set_slice> for cmd_temperature_set {
type Error = ();
fn try_from(input: cmd_temperature_set_slice) -> Result<Self, ()> {
Ok(Self::from_bytes(input))
}
}

impl TryFrom<&[u8]> for cmd_temperature_set {
type Error = ();
fn try_from(input: &[u8]) -> Result<Self, ()> {
assert!(input.len() >= size_of::<cmd_temperature_set_slice>());
let a: cmd_temperature_set_slice = input.try_into().unwrap();
Ok(Self::from_bytes(a))
}
}

}
"""
    assert expected == result
