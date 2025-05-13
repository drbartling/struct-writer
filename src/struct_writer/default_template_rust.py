import tomllib


def default_template():
    template = """
[file]
description = '''
/**
* @file
* @brief ${file.brief}
*
* ${file.description}
*
* @note This file is auto-generated using struct-writer
*/
'''
header = '''
pub use ${out_file.stem.lower()}::*;
mod ${out_file.stem.lower()} {
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(dead_code)]

use modular_bitfield::prelude::*;

#[cfg(feature = "std")]
use std::fmt::{Display, Formatter};

'''
footer = '''
}
'''

[enum]
header = '''
pub type ${enumeration.name}_slice = [u8;  ${enumeration.size}];
// ${enumeration.display_name}
// ${enumeration.description}
#[derive(
    Default, Debug, Clone, PartialEq, Copy,
)]${enumeration.unsigned_header}
pub enum ${enumeration.name} {
#[default]
'''
unsigned_header = '''
#[derive(BitfieldSpecifier)]
#[bits = ${enumeration.bits}]
'''
footer = '''
}

impl From<${enumeration.name}> for ${enumeration.name}_slice {
fn from(value: ${enumeration.name}) -> Self {
let v = value as ${enumeration.repr_type};
v.to_le_bytes()
}
}

impl TryFrom<&[u8]> for ${enumeration.name} {
type Error = ();
fn try_from(value: &[u8]) -> Result<Self, ()> {
assert!(value.len() >= size_of::<${enumeration.name}_slice>());
let v: ${enumeration.name}_slice = value[..size_of::<${enumeration.name}_slice>()]
.try_into()
.map_err(|_| ())?;
Self::try_from(v)
}
}

impl TryFrom<${enumeration.name}_slice> for ${enumeration.name} {
type Error = ();
fn try_from(value: ${enumeration.name}_slice) -> Result<Self, ()> {
let v = ${enumeration.repr_type}::from_le_bytes(value);
v.try_into()
}
}

impl TryFrom<${enumeration.repr_type}> for ${enumeration.name} {
type Error = ();
fn try_from(value: ${enumeration.repr_type}) -> Result<Self, ()> {
match value {
${enumeration.matches}
_ => Err(()),
}
}
}

'''
valued = '''
/// ${value.description}
${value.label} = ${value.value:#x},
'''

[group]
tag_name = '${group.name}_tag'

header = '''
pub type ${group.name}_slice = [u8;  ${group.max_size}];
// ${group.display_name}
// ${group.description}
#[repr(${group.repr_type})]
#[derive(Debug, Clone, PartialEq, )]
pub enum ${group.name} {
'''

[union]
header = '''
// ${union.display_name}
// ${union.description}
#[derive(Clone, PartialEq, Debug, PartialEq)]
pub enum ${union.name}{
'''
footer = '''
}

'''

[union.members]
default = '''
/// ${member.description}
${member.name}(${member.type}),
'''

[structure]
header = '''
pub type ${structure.name}_slice = [u8;  ${structure.size}];
// ${structure.display_name}
// ${structure.description}
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Debug, Clone, PartialEq,
)]
pub struct ${structure.name}{
'''
footer = '''
}

impl From<${structure.name}> for ${structure.name}_slice {
#[allow(unused_variables)]
fn from(value: ${structure.name}) -> Self {
#[allow(unused_mut)]
let mut buf: ${structure.name}_slice = [0; ${structure.size}];

${structure.serialization}

buf
}
}

impl TryFrom<${structure.name}_slice> for ${structure.name} {
type Error = ();
fn try_from(input: ${structure.name}_slice) -> Result<Self, ()> {
    let input: &[u8] = &input;
    input.try_into()
}
}

impl TryFrom<&[u8]> for ${structure.name} {
type Error = ();
fn try_from(input: &[u8]) -> Result<Self, ()> {
assert!(input.len() >= size_of::<${structure.name}_slice>());

Ok(Self{
${structure.deserialization}
})

}
}

'''

[structure.members.default]
definition = '''
/// ${member.description}
pub ${member.name}: ${member.type},
'''
serialize = '''
let temp: [u8; ${member.size}] = value.${member.name}.into();
buf[${buffer.start}..${buffer.end}].copy_from_slice(&temp);
'''
deserialize = '${member.name}: input[${buffer.start}..${buffer.end}].try_into()?,'

[structure.members.empty]
definition = '''
// Structure is intentionally empty (zero sized)
'''
serialize = ''
deserialize = ''

[structure.members.int]
definition = '''
/// ${member.description}
pub ${member.name}: i${member.size*8},
'''
serialize = 'buf[${buffer.start}..${buffer.end}].copy_from_slice(&value.${member.name}.to_le_bytes());'
deserialize = '${member.name}: i${member.size*8}::from_le_bytes(input[${buffer.start}..${buffer.end}].try_into().unwrap()),'

[structure.members.uint]
definition = '''
/// ${member.description}
pub ${member.name}: u${member.size*8},
'''
serialize = 'buf[${buffer.start}..${buffer.end}].copy_from_slice(&value.${member.name}.to_le_bytes());'
deserialize = '${member.name}: u${member.size*8}::from_le_bytes(input[${buffer.start}..${buffer.end}].try_into().unwrap()),'

[structure.members.bool]
definition = '''
/// ${member.description}
pub ${member.name}: bool,
'''
serialize = 'buf[${buffer.start}] = if value.${member.name}{1}else{0};'
deserialize = '${member.name}: if input[${buffer.start}] == 0 {false} else {true},'

[structure.members.bytes]
definition = '''
/// ${member.description}
pub ${member.name}: [u8; ${member.size}],
'''
serialize = 'buf[${buffer.start}..${buffer.end}].copy_from_slice(&value.${member.name});'
deserialize = '${member.name}: input[${buffer.start}..${buffer.end}].try_into().unwrap(),'

[structure.members.reserved]
definition = '''
/// ${member.description}
${member.name}: [u8; ${member.size}],
'''
serialize = 'buf[${buffer.start}..${buffer.end}].copy_from_slice(&[0_u8;${member.size}]);'
deserialize = '${member.name}: [0_u8;${member.size}],'

[structure.members.str]
definition = '''
/// ${member.description}
pub ${member.name}: [u8; ${member.size}],
'''
serialize = 'buf[${buffer.start}..${buffer.end}].copy_from_slice(&value.${member.name});'
deserialize = '${member.name}: input[${buffer.start}..${buffer.end}].try_into().unwrap(),'

[bit_field]
header = '''
pub type ${bit_field.name}_slice = [u8;  ${bit_field.size}];
// ${bit_field.display_name}
// ${bit_field.description}
#[bitfield]
#[cfg_attr(feature = "serde", derive(Serialize, Deserialize))]
#[derive(
    Debug, Clone, PartialEq, Copy,
)]
pub struct ${bit_field.name}{
'''
footer = '''
}

impl From<${bit_field.name}> for ${bit_field.name}_slice {
fn from(input: ${bit_field.name}) -> Self {
input.into_bytes()
}
}

impl TryFrom<${bit_field.name}_slice> for ${bit_field.name} {
type Error = ();
fn try_from(input: ${bit_field.name}_slice) -> Result<Self, ()> {
Ok(Self::from_bytes(input))
}
}

impl TryFrom<&[u8]> for ${bit_field.name} {
type Error = ();
fn try_from(input: &[u8]) -> Result<Self, ()> {
assert!(input.len() >= size_of::<${bit_field.name}_slice>());
let a: ${bit_field.name}_slice = input.try_into().unwrap();
Ok(Self::from_bytes(a))
}
}

'''
type_name = '${bit_field.name}_t'

[bit_field.members]
default = '''
/// ${member.description}
pub ${member.name}: ${member.type},
'''
reserved = '''
#[skip]
reserved_${member.start}: B${member.bits},
'''
uint = '''
/// ${member.description}
pub ${member.name}: B${member.bits},
'''

"""

    template = tomllib.loads(template)
    return template
