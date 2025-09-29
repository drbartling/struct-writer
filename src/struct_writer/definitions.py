import math
from dataclasses import dataclass
from typing import Any, Self, override


class ParseFailed(Exception):
    @override
    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__!s}({self.__dict__!r})"


class SizeMismatch(ParseFailed):
    """
    Exception raised the specified size of a type does not match the contents of the definition

    This can happen if a structure size does not equal the sum of its members

    >>> structure_definition = {
    ...     "simple_struct": {
    ...         "description": "A simple structure",
    ...         "display_name": "Simple Structure",
    ...         "type": "structure",
    ...         "size": 2,
    ...         "members": [
    ...             {
    ...                 "name": "number",
    ...                 "type": "int",
    ...                 "size": 1,
    ...                 "description": "A small number",
    ...             },
    ...         ],
    ...     }
    ... }
    >>> try:
    ...     TypeDefinitions.from_dict(structure_definition)
    ... except SizeMismatch as e:
    ...     print(e)
    Expected simple_struct to be size 2, but measured a size of 1 bytes

    If an enum value requires more bytes than the enum size

    >>> enum_definition = {
    ...     "an_enum": {
    ...         "description": "an example enum",
    ...         "display_name": "An Enum",
    ...         "type": "enum",
    ...         "size": 1,
    ...         "values": [
    ...             {
    ...                 "label": "a",
    ...                 "value": 256,
    ...                 "display_name": "A",
    ...                 "description": "The letter A",
    ...             }
    ...         ],
    ...     }
    ... }
    >>> try:
    ...     TypeDefinitions.from_dict(enum_definition)
    ... except SizeMismatch as e:
    ...     print(e)
    Expected an_enum to be size 1, but measured a size of 2 bytes

    And if a bitfield requires more bits

    >>> bitfield_definition = {
    ...     "a_bit_field": {
    ...         "description": "An example bit field",
    ...         "display_name": "A Bit Field",
    ...         "type": "bit_field",
    ...         "size": 1,
    ...         "members": [
    ...             {
    ...                 "name": "a_number",
    ...                 "start": 0,
    ...                 "end": 9,
    ...                 "bits": 9,
    ...                 "type": "uint",
    ...                 "description": "A 9 bit number",
    ...             },
    ...         ],
    ...     },
    ... }
    >>> try:
    ...     TypeDefinitions.from_dict(bitfield_definition)
    ... except SizeMismatch as e:
    ...     print(e)
    Expected a_bit_field to be size 1, but measured a size of 2 bytes


    """

    def __init__(
        self, name: str, expected_size: int, measured_size: float
    ) -> None:
        self.message: str = f"Expected {name} to be size {expected_size}, but measured a size of {measured_size} bytes"
        super().__init__(self.message)


class InvalidType(ParseFailed):
    """
    Exception raised when an invalid type is specified in a definition.

    >>> structure_definition = {
    ...     "empty_struct": {
    ...         "description": "An empty structure",
    ...         "display_name": "Empty Structure",
    ...         "type": "ssstructure",
    ...         "size": 0,
    ...     }
    ... }
    >>> try:
    ...     TypeDefinitions.from_dict(structure_definition)
    ... except InvalidType as e:
    ...     print(e)
    Invalid type (`ssstructure`) given for empty_struct
    """

    def __init__(self, name: str, def_type: str) -> None:
        self.message: str = f"Invalid type (`{def_type}`) given for {name}"
        super().__init__(self.message)


class RequiredFieldMissing(ParseFailed):
    """
    Exception raised when an invalid type is specified in a definition.

    If the type is missing we can't be more specific on what's missing from the
    type definition.

    >>> structure_definition = {
    ...     "empty_struct": {
    ...         "description": "An empty structure",
    ...         "display_name": "Empty Structure",
    ...         "size": 0,
    ...     }
    ... }
    >>> try:
    ...     TypeDefinitions.from_dict(structure_definition)
    ... except RequiredFieldMissing as e:
    ...     print(e)
    `MissingType` definition for `empty_struct` missing `type`

    But otherwise we give errors indicating what's missing from the definition

    >>> structure_definition = {
    ...     "empty_struct": {
    ...         "description": "An empty structure",
    ...         "display_name": "Empty Structure",
    ...         "type": "structure",
    ...     }
    ... }
    >>> try:
    ...     TypeDefinitions.from_dict(structure_definition)
    ... except RequiredFieldMissing as e:
    ...     print(e)
    `Structure` definition for `empty_struct` missing `size`

    And in the case that the member of an enum is missing a part, we give context:

    >>> enum_definition = {
    ...     "an_enum": {
    ...         "description": "an example enum",
    ...         "display_name": "An Enum",
    ...         "type": "enum",
    ...         "size": 1,
    ...         "values": [
    ...             {
    ...                 "label": "a",
    ...                 "value": 0,
    ...             }
    ...         ],
    ...     }
    ... }
    >>> try:
    ...     TypeDefinitions.from_dict(enum_definition)
    ... except RequiredFieldMissing as e:
    ...     print(e)
    `EnumValue` definition for `an_enum::a` missing `display_name`

    And the same is true when a structure member is missing an attribute

    >>> structure_definition = {
    ...     "simple_struct": {
    ...         "description": "A simple structure",
    ...         "display_name": "Simple Structure",
    ...         "type": "structure",
    ...         "size": 1,
    ...         "members": [
    ...             {
    ...                 "name": "number",
    ...                 "type": "int",
    ...                 "description": "A small number",
    ...             },
    ...         ],
    ...     }
    ... }
    >>> try:
    ...     TypeDefinitions.from_dict(structure_definition)
    ... except RequiredFieldMissing as e:
    ...     print(e)
    `StructureMember` definition for `simple_struct::number` missing `size`

    And the same is true when a bitfield member is missing an attribute

    >>> bitfield_definition = {
    ...     "a_bit_field": {
    ...         "description": "An example bit field",
    ...         "display_name": "A Bit Field",
    ...         "type": "bit_field",
    ...         "size": 1,
    ...         "members": [
    ...             {
    ...                 "name": "a_number",
    ...                 "start": 0,
    ...                 "end": 4,
    ...                 "bits": 4,
    ...                 "description": "A 4 bit number",
    ...             },
    ...             {
    ...                 "name": "reserved_4",
    ...                 "start": 4,
    ...                 "end": 8,
    ...                 "bits": 4,
    ...                 "type": "reserved",
    ...                 "description": "Unused bits",
    ...             },
    ...         ],
    ...     },
    ... }
    >>> try:
    ...     TypeDefinitions.from_dict(bitfield_definition)
    ... except RequiredFieldMissing as e:
    ...     print(e)
    `BitFieldMember` definition for `a_bit_field::a_number` missing `type`
    """

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


@dataclass
class DefinedType:
    description: str
    display_name: str
    name: str
    size: int

    @override
    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__!s}({self.__dict__!r})"

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    def as_bit_field(self) -> "BitField":
        raise NotImplementedError

    def as_group(self) -> "Group":
        raise NotImplementedError

    def as_structure(self) -> "Structure":
        raise NotImplementedError


@dataclass
class StructureMember:
    description: str
    name: str
    size: int
    type: str

    @classmethod
    def from_dict(cls, definition: dict[str, Any]) -> Self:
        try:
            return cls(
                description=definition.get("description", ""),
                name=definition["name"],
                size=definition["size"],
                type=definition["type"],
            )
        except KeyError as e:
            raise RequiredFieldMissing.from_key_error(
                definition.get("name", "missing_name"),
                cls.__name__,
                e,
            ) from e

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "name": self.name,
            "size": self.size,
            "type": self.type,
        }


@dataclass
class Structure(DefinedType):
    members: list[StructureMember]

    @classmethod
    def from_dict(cls, definition: dict[str, dict[str, Any]]) -> Self:
        (name, inner) = next(iter(definition.items()))
        return cls.from_named_dict(name, inner)

    @classmethod
    def from_named_dict(cls, name: str, definition: dict[str, Any]) -> Self:
        try:
            members = [
                StructureMember.from_dict(m)
                for m in definition.get("members", [])
            ]
        except RequiredFieldMissing as e:
            def_type = f"{name}::{e.def_type}"
            raise RequiredFieldMissing(def_type, e.name, e.field) from e

        measured_size = sum(m.size for m in members)
        try:
            self = cls(
                description=definition.get("description", ""),
                display_name=definition["display_name"],
                members=members,
                name=name,
                size=definition["size"],
            )
        except KeyError as e:
            raise RequiredFieldMissing.from_key_error(
                name, cls.__name__, e
            ) from e
        if measured_size != self.size:
            raise SizeMismatch(name, self.size, measured_size)
        return self

    @override
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "display_name": self.display_name,
            "size": self.size,
            "type": "structure",
            "members": [member.to_dict() for member in self.members],
        }

    @override
    def as_structure(self) -> Self:
        return self


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
                description=definition.get("description", ""),
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "value": self.value,
            "display_name": self.display_name,
            "description": self.description,
        }


@dataclass
class Enumeration(DefinedType):
    values: list[EnumValue]

    @classmethod
    def from_named_dict(cls, name: str, definition: dict[str, Any]) -> Self:
        values: list[EnumValue] = []
        next_int = 0
        for v in definition.get("values", []):
            try:
                ev = EnumValue.from_partial_dict(v, next_int)
            except RequiredFieldMissing as e:
                def_type = f"{name}::{e.def_type}"
                raise RequiredFieldMissing(def_type, e.name, e.field) from e
            next_int = ev.value + 1
            values.append(ev)
        bits = cls.enum_bits([v.value for v in values])
        measured_size = math.ceil(bits / 8.0)
        try:
            enum_size: int = definition["size"]
        except KeyError as e:
            raise RequiredFieldMissing.from_key_error(
                definition.get("name", "missing_name"),
                cls.__name__,
                e,
            ) from e

        if measured_size > enum_size:
            raise SizeMismatch(name, enum_size, measured_size)
        return cls(
            description=definition.get("description", ""),
            display_name=definition["display_name"],
            values=values,
            name=name,
            size=enum_size,
        )

    @staticmethod
    def enum_bits(values: list[int]) -> int:
        """
        >>> Enumeration.enum_bits([0, 0])
        1
        >>> Enumeration.enum_bits([0, 255])
        8
        >>> Enumeration.enum_bits([0, 256])
        9
        >>> Enumeration.enum_bits([-1, 127])
        8
        >>> Enumeration.enum_bits([-128, 127])
        8
        >>> Enumeration.enum_bits([-129, 127])
        9
        >>> Enumeration.enum_bits([-128, 128])
        9
        """
        min_value = min(values)
        max_value = max(values)
        if 0 == min_value and 0 == max_value:
            return 1
        is_signed = 0 > min_value
        if not is_signed:
            return math.ceil(math.log2(max_value + 1))
        max_val = max(abs(min_value), max_value + 1)
        return math.ceil(math.log2(max_val)) + 1

    @override
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "display_name": self.display_name,
            "size": self.size,
            "type": "enum",
            "values": [v.to_dict() for v in self.values],
        }


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
                description=definition.get("description", ""),
            )
        except KeyError as e:
            raise RequiredFieldMissing.from_key_error(
                definition.get("name", "missing_name"),
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "bits": self.bits,
            "size": math.ceil(self.bits / 8),
            "type": self.type,
            "description": self.description,
        }


@dataclass
class BitField(DefinedType):
    members: list[BitFieldMember]

    @classmethod
    def from_named_dict(cls, name: str, definition: dict[str, Any]) -> Self:
        members: list[BitFieldMember] = []
        start_bit = 0
        for m in definition.get("members", []):
            if start_bit < m.get("start", start_bit):
                members.append(BitFieldMember.reserved(start_bit, m["start"]))
            try:
                bfm = BitFieldMember.from_partial_dict(m, start_bit)
            except RequiredFieldMissing as e:
                def_type = f"{name}::{e.def_type}"
                raise RequiredFieldMissing(def_type, e.name, e.field) from e
            start_bit = bfm.end
            members.append(bfm)
        structure_size: int = definition["size"]
        expected_bits: int = structure_size * 8
        measured_bits = sum(m.bits for m in members)
        if measured_bits > expected_bits:
            raise SizeMismatch(
                name, structure_size, math.ceil(measured_bits / 8.0)
            )
        reserved_bits = expected_bits - measured_bits
        if measured_bits < expected_bits:
            members.append(
                BitFieldMember.reserved(start_bit, start_bit + reserved_bits)
            )

        return cls(
            description=definition.get("description", ""),
            display_name=definition["display_name"],
            members=members,
            name=name,
            size=structure_size,
        )

    @override
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "display_name": self.display_name,
            "size": self.size,
            "type": "bit_field",
            "members": [m.to_dict() for m in self.members],
        }

    @override
    def as_bit_field(self) -> Self:
        return self


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

    @override
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "display_name": self.display_name,
            "size": self.size,
            "type": "group",
        }

    @override
    def as_group(self) -> Self:
        return self


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
            description=definition.get("description", ""),
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
            try:
                definition_type: str = v["type"]
            except KeyError as e:
                def_type = "MissingType"
                raise RequiredFieldMissing.from_key_error(k, def_type, e) from e
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
