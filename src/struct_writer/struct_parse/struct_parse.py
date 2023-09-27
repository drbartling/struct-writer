import logging

_logger = logging.getLogger(__name__)


def element_into_bytes(element, definitions, endianness="big"):
    element_name = list(element.keys())[0]
    b = b""
    if definition := definitions.get(element_name):
        if "group" == definition["type"]:
            b += group_into_bytes(element, definitions, endianness)
        if "structure" == definition["type"]:
            b += structure_into_bytes(element, definitions, endianness)
        if "enum" == definition["type"]:
            b += enum_into_bytes(element, definitions, endianness)
    else:
        b += primitive_to_bytes(element, endianness)

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
        member = {
            member_type: {
                "value": member_value,
                "size": member_size,
            }
        }
        b += element_into_bytes(member, definitions, endianness)

    return b


def enum_into_bytes(element, definitions, endianness):
    enum_name = list(element.keys())[0]
    enum_value = list(element.values())[0]["value"]
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
                signed=False,
            )
        counter += 1

    return b


def primitive_to_bytes(element, endianness):
    type_name = list(element.keys())[0]
    value = list(element.values())[0]
    if "int" == type_name:
        return int(value["value"]).to_bytes(
            value["size"], byteorder=endianness, signed=True
        )
    if "uint" == type_name:
        return int(value["value"]).to_bytes(
            value["size"], byteorder=endianness, signed=False
        )
    if "bytes" == type_name:
        assert isinstance(value["value"], bytes)
        assert len(value["value"]) == value["size"]
        return value["value"]
    if "str" == type_name:
        assert isinstance(value["value"], str)
        b_str = str(value["value"]).encode("utf-8")
        diff = value["size"] - len(b_str)
        if 0 < diff:
            b_str += b"\x00" * diff
        if 0 > diff:
            b_str = b_str[0 : value["size"]]
            _logger.warning("Truncating string to %s", b_str)
        return primitive_to_bytes(
            {"bytes": {"value": b_str, "size": value["size"]}}, endianness
        )
    raise ValueError(f"type: {type_name} is not handled")  # pragma: no cover
