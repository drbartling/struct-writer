import logging
import math
from typing import Any

from struct_writer import generate_structured_code

_logger = logging.getLogger(__name__)


def element_into_bytes(element, definitions, endianness="big", size=None):
    element_name = list(element.keys())[0]
    b = b""
    if definition := definitions.get(element_name):
        if "group" == definition["type"]:
            b += group_into_bytes(element, definitions, endianness)
        if "structure" == definition["type"]:
            b += structure_into_bytes(element, definitions, endianness)
        if "enum" == definition["type"]:
            b += enum_into_bytes(element, definitions, endianness)
        if "bit_field" == definition["type"]:
            b += bit_field_into_bytes(element, definitions, endianness)
    else:
        b += primitive_to_bytes(element, endianness, size)

    return b


def group_into_bytes(element, definitions, endianness):
    group_name = list(element.keys())[0]
    group_member_name = list(element[group_name].keys())[0]

    b = b""

    group_elements = {
        k: v
        for k, v in definitions.items()
        if group_name in v.get("groups", {})
    }
    member_definition = group_elements[group_member_name]
    tag = member_definition["groups"][group_name]["value"]
    b += tag.to_bytes(1)

    for e_name, e_value in element[group_name].items():
        b += element_into_bytes({e_name: e_value}, definitions, endianness)

    return b


def structure_into_bytes(element, definitions, endianness):
    struct_name = list(element.keys())[0]
    struct_members = list(element.values())[0]
    struct_definition = definitions[struct_name]

    b = b""
    for member_definition in struct_definition.get("members", []):
        member_name = member_definition["name"]
        member_value = struct_members[member_name]
        member_type = member_definition["type"]
        member_size = member_definition["size"]
        member = {member_type: member_value}
        b += element_into_bytes(member, definitions, endianness, member_size)

    return b


def enum_into_bytes(element, definitions, endianness):
    enum_name = list(element.keys())[0]
    enum_value = list(element.values())[0]
    enum_definition = definitions[enum_name]
    b = b""

    counter = 0
    for value in enum_definition["values"]:
        if value.get("value") is not None:
            counter = value["value"]
        if value["label"] == enum_value:
            b = int(counter).to_bytes(
                length=enum_definition["size"],
                byteorder=endianness,
                signed=enum_definition.get("signed", False),
            )
            assert parse_enum(b, enum_name, definitions, endianness)
        counter += 1

    return b


def bit_field_into_bytes(element, definitions, endianness):
    bit_field_name = list(element.keys())[0]
    bit_field_members = list(element.values())[0]
    bit_field_definition = definitions[bit_field_name]

    raw_value = 0
    for member_definition in bit_field_definition.get("members", []):
        generate_structured_code.complete_bit_field_member(member_definition)
        member_name = member_definition["name"]
        member_value = bit_field_members[member_name]
        member_type = member_definition["type"]
        member_size = bit_field_definition["size"]
        member = {member_type: member_value}
        byte_value: bytes = element_into_bytes(
            member, definitions, endianness, member_size
        )
        v = int.from_bytes(byte_value, endianness)
        mask = int("1" * member_definition["bits"], 2)
        v = v & mask
        v = v << member_definition["start"]

        raw_value += v
    b = raw_value.to_bytes(bit_field_definition["size"], endianness)

    return b


def primitive_to_bytes(element, endianness, size):
    type_name = list(element.keys())[0]
    value = list(element.values())[0]
    if "int" == type_name:
        return int(value).to_bytes(size, byteorder=endianness, signed=True)
    if "uint" == type_name:
        return int(value).to_bytes(size, byteorder=endianness, signed=False)
    if "bytes" == type_name:
        assert isinstance(value, bytes)
        assert len(value) == size
        return value
    if "str" == type_name:
        assert isinstance(value, str)
        b_str = str(value).encode("utf-8")
        diff = size - len(b_str)
        if 0 < diff:
            b_str += b"\x00" * diff
        if 0 > diff:
            b_str = b_str[0:size]
            _logger.warning("Truncating string to %s", b_str)
        return primitive_to_bytes({"bytes": b_str}, endianness, size)
    raise ValueError(f"type: {type_name} is not handled")  # pragma: no cover


def parse_bytes(byte_data, type_name, definitions, endianness="big"):
    try:
        if definition := definitions.get(type_name):
            definition_type = definition["type"]
            if "structure" == definition_type:
                return parse_struct(
                    byte_data, type_name, definitions, endianness
                )
            if "enum" == definition_type:
                return parse_enum(byte_data, type_name, definitions, endianness)
            if "group" == definition_type:
                return parse_group(
                    byte_data, type_name, definitions, endianness
                )
            if "bit_field" == definition_type:
                return parse_bit_field(
                    byte_data, type_name, definitions, endianness
                )
        return parse_primitive(byte_data, type_name, endianness)
    except Exception as _e:  # pylint: disable=broad-exception-caught
        _logger.exception("e")
        return parse_primitive(byte_data, "bytes", endianness)


def parse_struct(byte_data, struct_name, definitions, endianness):
    definition = definitions[struct_name]
    assert "structure" == definition["type"]
    assert (
        len(byte_data) == definition["size"]
    ), f'Expected {definition["size"]} bytes for `{struct_name}`, found {len(byte_data)}'

    members = definition.get("members", [])
    parsed_members = {}
    for member in members:
        member_bytes = byte_data[: member["size"]]
        byte_data = byte_data[member["size"] :]
        parsed_members[member["name"]] = parse_bytes(
            member_bytes, member["type"], definitions, endianness
        )
    return parsed_members


def parse_enum(
    byte_data: bytes,
    enum_name: str,
    definitions: dict[str, Any],
    endianness: str,
):
    definition = definitions[enum_name]
    assert "enum" == definition["type"]
    values = definition["values"]
    is_signed: bool = definition.get("signed", False)
    int_value = int.from_bytes(byte_data, endianness, signed=is_signed)
    counter = 0
    for v in values:
        enum_value = v.get("value", counter)
        counter = enum_value + 1
        if int_value == enum_value:
            return v["label"]
    raise ValueError(f"`{int_value}` not found in enum `{enum_name}`")


def parse_group(
    byte_data: bytes,
    group_name: str,
    definitions: dict[str, Any],
    endianness: str,
):
    definition = definitions[group_name]
    assert "group" == definition["type"]

    group_tag = byte_data[: definition["size"]]
    byte_data = byte_data[definition["size"] :]
    group_tag = int.from_bytes(group_tag, endianness)

    for element_name, element_definition in definitions.items():
        if element_groups := element_definition.get("groups"):
            if element_group := element_groups.get(group_name):
                if element_group["value"] == group_tag:
                    parsed_element = parse_bytes(
                        byte_data, element_name, definitions, endianness
                    )
                    return {element_name: parsed_element}
    raise ValueError(f"`{group_tag}` not found in group `{group_name}`")


def parse_bit_field(
    byte_data: bytes,
    bit_field_name: str,
    definitions: dict[str, Any],
    endianness: str,
):
    definition = definitions[bit_field_name]
    assert "bit_field" == definition["type"]

    byte_value: int = int.from_bytes(byte_data, endianness, signed=False)

    parsed_members = {}
    for member in definition.get("members", []):
        if member_definition := definitions.get(member["type"]):
            is_signed = member_definition.get("signed", False)
        else:
            is_signed = "int" == member["type"]
        generate_structured_code.complete_bit_field_member(member)
        mask = int("1" * member["bits"], 2)
        bits_value = byte_value >> member["start"]
        bits_value: int = bits_value & mask
        if is_signed:
            msb = int("1" + "0" * (member["bits"] - 1), 2)
            is_negative = bits_value & msb
            if is_negative:
                bits_value = bits_value | (~mask)
        size = math.ceil(member["bits"] / 8.0)
        masked_bytes = bits_value.to_bytes(length=size, signed=is_signed)
        parsed_members[member["name"]] = parse_bytes(
            masked_bytes, member["type"], definitions, endianness
        )
    return parsed_members


def parse_primitive(byte_data: bytes, type_name: str, endianness: str):
    if "int" == type_name:
        return int.from_bytes(byte_data, endianness, signed=True)
    if "uint" == type_name:
        return int.from_bytes(byte_data, endianness, signed=False)
    if "bytes" == type_name:
        return (
            R" ".join([f"{b:02X}" for b in byte_data])
            + f" (len={len(byte_data)})"
        )
    if "str" == type_name:
        return byte_data.decode("utf-8").strip("\x00")
    raise ValueError(f"type: {type_name} is not handled")  # pragma: no cover
