import logging
import math
import warnings
from typing import Any, Literal

_logger = logging.getLogger(__name__)


def element_into_bytes(
    element: dict[str, Any],
    definitions: dict[str, Any],
    endianness: Literal["little", "big"] = "big",
    size: int | None = None,
) -> bytes:
    result = _element_into_bytes(element, definitions, endianness, size)
    _logger.debug("\ninput: %s\nbytes: %s\n", element, bytes_to_str(result))
    return result


def _element_into_bytes(
    element: dict[str, Any],
    definitions: dict[str, Any],
    endianness: Literal["little", "big"] = "big",
    size: int | None = None,
) -> bytes:
    element_name = next(iter(element.keys()))
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
        if size is None:
            msg = f"Size must be provided for primitive element: {element}"
            raise ValueError(msg)
        b += primitive_to_bytes(element, endianness, size)

    return b


def group_into_bytes(
    element: dict[str, Any],
    definitions: dict[str, Any],
    endianness: Literal["little", "big"],
) -> bytes:
    group_name = next(iter(element.keys()))
    group_member_name = next(iter(element[group_name].keys()))

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


def structure_into_bytes(
    element: dict[str, Any],
    definitions: dict[str, Any],
    endianness: Literal["little", "big"],
) -> bytes:
    struct_name = next(iter(element.keys()))
    struct_members = next(iter(element.values()))
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


def enum_into_bytes(
    element: dict[str, Any],
    definitions: dict[str, Any],
    endianness: Literal["little", "big"],
) -> bytes:
    enum_name = next(iter(element.keys()))
    enum_value = next(iter(element.values()))
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


def complete_enums(enum_definition: dict[str, Any]) -> dict[str, Any]:
    if enum_definition.get("complete"):
        return enum_definition
    _logger.debug("Input enum definition: %s", enum_definition)
    counter = 0
    for value in enum_definition["values"]:
        if value.get("value"):
            counter = value["value"]
        else:
            value["value"] = counter
        counter += 1

    bits = math.ceil(math.log2(counter))
    signed = (
        1
        if any(v.get("value", 0) < 0 for v in enum_definition.get("values", []))
        else 0
    )
    bits += signed
    enum_definition["bits"] = bits

    enum_definition["complete"] = True
    _logger.debug("Completed enum definition: %s", enum_definition)
    return enum_definition


def bit_field_into_bytes(
    element: dict[str, Any],
    definitions: dict[str, Any],
    endianness: Literal["little", "big"],
) -> bytes:
    bit_field_name = next(iter(element.keys()))
    bit_field_members = next(iter(element.values()))
    bit_field_definition = definitions[bit_field_name]

    raw_value = 0
    for member_definition in bit_field_definition.get("members", []):
        complete_bit_field_member(
            member_definition, bit_field_definition["size"]
        )
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

    return raw_value.to_bytes(bit_field_definition["size"], endianness)


def primitive_to_bytes(
    element: dict[str, Any],
    endianness: Literal["little", "big"],
    size: int,
) -> bytes:
    type_name = next(iter(element.keys()))
    value = next(iter(element.values()))
    if "int" == type_name:
        return int(value).to_bytes(size, byteorder=endianness, signed=True)
    if "uint" == type_name:
        return int(value).to_bytes(size, byteorder=endianness, signed=False)
    if "bytes" == type_name:
        assert isinstance(value, bytes)
        assert len(value) == size
        return value
    if "reserved" == type_name:
        return b"\xff" * size
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
    msg = f"type: {type_name} is not handled"
    raise ValueError(msg)  # pragma: no cover


def parse_bytes(
    byte_data: bytes,
    type_name: str,
    definitions: dict[str, Any],
    endianness: Literal["little", "big"] = "big",
) -> dict[str, Any] | str | int:
    result = _parse_bytes(byte_data, type_name, definitions, endianness)
    _logger.debug(
        "\n`%s` from `%s`\n%s", type_name, bytes_to_str(byte_data), result
    )
    return result


def _parse_bytes(
    byte_data: bytes,
    type_name: str,
    definitions: dict[str, Any],
    endianness: Literal["little", "big"] = "big",
) -> dict[str, Any] | str | int:
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
    except Exception as e:  # noqa: BLE001
        msg = f"Failed to parse {type_name}, caused by {e}"
        _logger.error(msg)
        return parse_primitive(byte_data, "bytes", endianness)


def parse_struct(
    byte_data: bytes,
    struct_name: str,
    definitions: dict[str, Any],
    endianness: Literal["little", "big"],
) -> dict[str, Any]:
    definition = definitions[struct_name]
    assert "structure" == definition["type"]
    assert len(byte_data) == definition["size"], (
        f"Expected {definition['size']} bytes for `{struct_name}`, "
        f"found {len(byte_data)}"
    )

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
    endianness: Literal["little", "big"],
) -> str:
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
    msg = f"`{int_value}` not found in enum `{enum_name}`"
    raise ValueError(msg)


def parse_group(
    byte_data: bytes,
    group_name: str,
    definitions: dict[str, Any],
    endianness: Literal["little", "big"],
) -> dict[str, Any]:
    definition = definitions[group_name]
    assert "group" == definition["type"]

    tag_start = definition.get("offset", 0)
    warn_deprecated_offset(group_name, tag_start)
    tag_end = tag_start + definition["size"]
    group_tag = byte_data[tag_start:tag_end]
    _logger.debug("group_tag: `%s`", group_tag)

    byte_data = byte_data[:tag_start] + byte_data[tag_end:]
    _logger.debug("group byte_data: `%s`", byte_data)

    group_tag = int.from_bytes(group_tag, endianness)

    for element_name, element_definition in definitions.items():
        if (
            (element_groups := element_definition.get("groups"))
            and (element_group := element_groups.get(group_name))
            and (element_group["value"] == group_tag)
        ):
            parsed_element = parse_bytes(
                byte_data, element_name, definitions, endianness
            )
            return {element_name: parsed_element}
    msg = f"`{group_tag}` not found in group `{group_name}`"
    raise ValueError(msg)


def warn_deprecated_offset(
    group_name: str,
    tag_start: int,
    _warned: dict = {},  # noqa: B006
) -> bool:
    if _warned.get(group_name, False):
        return False

    if 0 == tag_start:
        return False

    _warned[group_name] = True
    warnings.warn(
        f"Group `{group_name}` tag has an offset of {tag_start} bytes.  "
        "It's not recommended to do this except for backwards "
        "compatibility reasons",
        category=DeprecationWarning,
        stacklevel=5,
    )
    return True


def parse_bit_field(
    byte_data: bytes,
    bit_field_name: str,
    definitions: dict[str, Any],
    endianness: Literal["little", "big"],
) -> dict[str, Any]:
    definition = definitions[bit_field_name]
    assert "bit_field" == definition["type"]

    byte_value: int = int.from_bytes(byte_data, endianness, signed=False)

    parsed_members = {}
    if not definition.get("members", []):
        _logger.warning("Bitfield `%s` has no members", bit_field_name)
    for member in definition.get("members", []):
        if member_definition := definitions.get(member["type"]):
            is_signed = member_definition.get("signed", False)
        else:
            is_signed = "int" == member["type"]
        complete_bit_field_member(member, definition["size"])
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


def complete_bit_field_member(
    bit_field_member: dict, bit_field_size: int
) -> dict:
    assert "start" in bit_field_member
    assert 0 <= bit_field_member["start"]

    if "last" not in bit_field_member and "bits" not in bit_field_member:
        try:
            bit_field_member["last"] = bit_field_member["start"]
        except:  # pragma: no cover
            _logger.exception(str(bit_field_member))
            raise
        bit_field_member["bits"] = 1
    if "last" not in bit_field_member:
        try:
            bit_field_member["last"] = (
                bit_field_member["start"] + bit_field_member["bits"] - 1
            )
        except:  # pragma: no cover
            _logger.exception(str(bit_field_member))
            raise
    if "bits" not in bit_field_member:
        try:
            bit_field_member["bits"] = (
                bit_field_member["last"] - bit_field_member["start"] + 1
            )
        except:  # pragma: no cover
            _logger.exception(str(bit_field_member))
            raise
    assert (
        bit_field_member["last"]
        == bit_field_member["start"] + bit_field_member["bits"] - 1
    )
    assert (
        bit_field_member["bits"]
        == bit_field_member["last"] - bit_field_member["start"] + 1
    )
    assert bit_field_member["last"] / 8.0 <= bit_field_size, (
        f"{bit_field_member['last']} bits do not fit in {bit_field_size} byte{'' if bit_field_size == 1 else 's'}"
    )

    return bit_field_member


def parse_primitive(  # noqa: PLR0911
    byte_data: bytes, type_name: str, endianness: Literal["little", "big"]
) -> int | bool | str:
    if "int" == type_name:
        _logger.debug("byte_data: `%s`", byte_data)
        return int.from_bytes(byte_data, endianness, signed=True)
    if "uint" == type_name:
        return int.from_bytes(byte_data, endianness, signed=False)
    if "bool" == type_name:
        val = int.from_bytes(byte_data, endianness, signed=False)
        if 0 == val:
            return False
        if 1 == val:
            return True
        return f"True(ish): 0x{val:02X}"
    if type_name in {"bytes", "reserved"}:
        return bytes_to_str(byte_data)
    if "str" == type_name:
        return byte_data.decode("utf-8").strip("\x00")
    msg = f"type: {type_name} is not handled"
    raise ValueError(msg)  # pragma: no cover


def bytes_to_str(data: bytes) -> str:
    return R" ".join([f"{b:02X}" for b in data]) + f" (len={len(data)})"
