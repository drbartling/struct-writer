import math
from dataclasses import dataclass
from typing import Any, Self, override


class ParseFailed(Exception):
    @override
    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__!s}({self.__dict__!r})"


class SizeMismatch(ParseFailed):
    def __init__(
        self, name: str, expected_size: int, measured_size: float
    ) -> None:
        self.message: str = f"Expected {name} to be size {expected_size}, but measured a size of {measured_size} bytes"
        super().__init__(self.message)


class InvalidType(ParseFailed):
    """ """

    def __init__(self, name: str, def_type: str) -> None:
        self.message: str = f"Invalid type (`{def_type}`) given for {name}"
        super().__init__(self.message)


class RequiredFieldMissing(ParseFailed):
    def __init__(self, def_type: str, name: str, field: str) -> None:
        self.def_type: str = def_type
        self.name: str = name
        self.field: str = field
        self.message: str = (
            f"`{name}` definition for `{def_type}` missing `{field}`"
        )
        super().__init__(self.message)

    @classmethod
    def from_key_error(
        cls, def_type: str, name: str, key_error: KeyError
    ) -> Self:
        return cls(def_type, name, key_error.args[0])


class DefinedType:
    @override
    def __repr__(self) -> str:
        return f"{self.__class__!s}({self.__dict__!r})"


@dataclass
class StructureMember:
    description: str
    name: str
    size: int
    type: str

    @classmethod
    def from_dict(cls, definition: dict[str, Any]) -> Self:
        return cls(
            description=definition["description"],
            name=definition["name"],
            size=definition["size"],
            type=definition["type"],
        )


@dataclass
class Structure(DefinedType):
    description: str
    display_name: str
    members: list[StructureMember]
    name: str
    size: int

    @classmethod
    def from_dict(cls, definition: dict[str, dict[str, Any]]) -> Self:
        (name, inner) = next(iter(definition.items()))
        return cls.from_named_dict(name, inner)

    @classmethod
    def from_named_dict(cls, name: str, definition: dict[str, Any]) -> Self:
        members = [
            StructureMember.from_dict(m) for m in definition.get("members", [])
        ]
        measured_size = sum(m.size for m in members)
        structure_size = definition["size"]
        if measured_size != structure_size:
            raise SizeMismatch(name, structure_size, measured_size)
        return cls(
            description=definition["description"],
            display_name=definition["display_name"],
            members=members,
            name=name,
            size=structure_size,
        )


@dataclass
class EnumValue:
    label: str
    value: int
    display_name: str
    description: str

    @classmethod
    def from_dict(cls, definition: dict[str, Any]) -> Self:
        try:
            return cls(
                label=definition["label"],
                value=definition["value"],
                display_name=definition["display_name"],
                description=definition["description"],
            )
        except KeyError as e:
            raise RequiredFieldMissing.from_key_error(
                definition.get("label", "missing_label"),
                cls.__name__,
                e,
            ) from e

    @classmethod
    def from_partial_dict(
        cls, definition: dict[str, Any], default_val: int
    ) -> Self:
        definition["value"] = definition.get("value", default_val)
        return cls.from_dict(definition)


@dataclass
class Enumeration(DefinedType):
    name: str
    values: list[EnumValue]
    description: str
    display_name: str
    size: int

    @classmethod
    def from_named_dict(cls, name: str, definition: dict[str, Any]) -> Self:
        values: list[EnumValue] = []
        next_int = 0
        try:
            for v in definition.get("values", []):
                ev = EnumValue.from_partial_dict(v, next_int)
                next_int = ev.value + 1
                values.append(ev)
        except RequiredFieldMissing as e:
            def_type = f"{name}::{e.def_type}"
            raise RequiredFieldMissing(def_type, e.name, e.field) from e
        is_signed = min(v.value for v in values) < 0
        max_val = max(abs(v.value) for v in values)
        bits = math.ceil(math.log2(max_val))
        bits = bits + 2 if is_signed else bits + 1
        measured_size = math.ceil(bits / 8.0)
        enum_size = definition["size"]
        if measured_size != enum_size:
            raise SizeMismatch(name, enum_size, measured_size)
        return cls(
            description=definition["description"],
            display_name=definition["display_name"],
            values=values,
            name=name,
            size=enum_size,
        )


@dataclass
class BitFieldMember:
    name: str
    start: int
    end: int
    bits: int
    type: str
    description: str

    @classmethod
    def from_dict(cls, definition: dict[str, Any]) -> Self:
        try:
            return cls(
                name=definition["name"],
                start=definition["start"],
                end=definition["end"],
                bits=definition["bits"],
                type=definition["type"],
                description=definition["description"],
            )
        except KeyError as e:
            raise RequiredFieldMissing.from_key_error(
                definition.get("label", "missing_label"),
                cls.__name__,
                e,
            ) from e

    @classmethod
    def from_partial_dict(
        cls,
        definition: dict[str, Any],
        default_start: int,
        default_bits: int = 1,
    ) -> Self:
        definition["start"] = definition.get("start", default_start)
        if end := definition.get("end"):
            definition["bits"] = definition.get(
                "bits", end - definition["start"]
            )
        else:
            definition["bits"] = definition.get("bits", default_bits)
            definition["end"] = definition["start"] + definition["bits"]
        return cls.from_dict(definition)

    @classmethod
    def reserved(cls, start: int, end: int) -> Self:
        bits = end - start
        return cls(
            name=f"reserved_{start}",
            start=start,
            end=end,
            bits=bits,
            type="reserved",
            description="Reserved",
        )


@dataclass
class BitField(DefinedType):
    description: str
    display_name: str
    members: list[BitFieldMember]
    name: str
    size: int

    @classmethod
    def from_dict(cls, definition: dict[str, dict[str, Any]]) -> Self:
        (name, inner) = next(iter(definition.items()))
        return cls.from_named_dict(name, inner)

    @classmethod
    def from_named_dict(cls, name: str, definition: dict[str, Any]) -> Self:
        members: list[BitFieldMember] = []
        start_bit = 0
        for m in definition.get("members", []):
            if start_bit < m.get("start", start_bit):
                members.append(BitFieldMember.reserved(start_bit, m["start"]))
            bfm = BitFieldMember.from_partial_dict(m, start_bit)
            start_bit = bfm.end
            members.append(bfm)
        structure_size: int = definition["size"]
        expected_bits: int = structure_size * 8
        measured_bits = sum(m.bits for m in members)
        if measured_bits > expected_bits:
            raise SizeMismatch(name, structure_size, measured_bits / 8.0)
        reserved_bits = expected_bits - measured_bits
        if measured_bits < expected_bits:
            members.append(
                BitFieldMember.reserved(start_bit, start_bit + reserved_bits)
            )

        return cls(
            description=definition["description"],
            display_name=definition["display_name"],
            members=members,
            name=name,
            size=structure_size,
        )


@dataclass
class GroupMember:
    # The name used within the group
    # e.g. the variable name for the member in a C union
    name: str
    # The name of the type this member is
    type: str
    # The TAG value used to descriminate the type
    value: int

    @classmethod
    def from_named_dict(cls, name: str, dictionary: dict[str, Any]) -> Self:
        return cls(
            name=dictionary["name"],
            type=name,
            value=dictionary["value"],
        )


@dataclass
class Group(DefinedType):
    """
    A Tagged Union of a group of structures

    https://en.wikipedia.org/wiki/Tagged_union

    """

    name: str
    display_name: str
    description: str
    size: int
    members: list[GroupMember]

    @classmethod
    def from_definitions(
        cls, group_name: str, definitions: dict[str, Any]
    ) -> Self:
        members = [
            k
            for (k, v) in definitions.items()
            if group_name in v.get("groups", {})
        ]
        members = {m: definitions[m]["groups"][group_name] for m in members}
        members = [
            GroupMember.from_named_dict(k, v) for (k, v) in members.items()
        ]
        group_definition = definitions[group_name]
        return cls(
            name=group_name,
            display_name=group_definition["display_name"],
            description=group_definition["description"],
            size=group_definition["size"],
            members=members,
        )


@dataclass
class FileDescription:
    brief: str
    description: str

    @override
    def __repr__(self) -> str:
        return f"{self.__class__!s}({self.__dict__!r})"

    @classmethod
    def from_dict(cls, definition: dict[str, Any]) -> Self:
        return cls(
            brief=definition["brief"],
            description=definition["description"],
        )

    @classmethod
    def empty(cls) -> Self:
        return cls(brief="", description="")


@dataclass
class TypeDefinitions:
    file_info: FileDescription
    definitions: dict[str, DefinedType]

    @override
    def __repr__(self) -> str:
        return f"{self.__class__!s}({self.__dict__!r})"

    @classmethod
    def from_dict(cls, definitions: dict[str, Any]) -> Self:
        result: dict[str, DefinedType] = {}
        file_info = definitions.pop("file", {"brief": "", "description": ""})
        file_info = FileDescription.from_dict(file_info)
        for k, v in definitions.items():
            definition_type: str = v.get("type")
            match definition_type:
                case "bit_field":
                    result[k] = BitField.from_named_dict(k, v)
                case "enum":
                    result[k] = Enumeration.from_named_dict(k, v)
                case "group":
                    result[k] = Group.from_definitions(k, definitions)
                case "structure":
                    result[k] = Structure.from_named_dict(k, v)
                case _:
                    raise InvalidType(k, definition_type)

        return cls(file_info, result)
