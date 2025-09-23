from dataclasses import dataclass
from typing import Any, Self, override

from devtools import debug


class ParseFailed(Exception):
    @override
    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__!s}({self.__dict__!r})"


class SizeMismatch(ParseFailed):
    def __init__(
        self, name: str, expected_size: int, measured_size: int
    ) -> None:
        self.message: str = f"Expected {name} to be size {expected_size}, but the sum of it's members is {measured_size}"
        super().__init__(self.message)


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

    @override
    def __repr__(self) -> str:
        return f"{self.__class__!s}({self.__dict__!r})"

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

    @override
    def __repr__(self) -> str:
        return f"{self.__class__!s}({self.__dict__!r})"

    @classmethod
    def from_dict(cls, definition: dict[str, dict[str, Any]]) -> Self:
        (name, inner) = next(iter(definition.items()))
        return cls.from_named_dict(name, inner)

    @classmethod
    def from_named_dict(cls, name: str, definition: dict[str, Any]) -> Self:
        debug(name)
        debug(definition)
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
class TypeDefinitions:
    definitions: dict[str, DefinedType]

    @override
    def __repr__(self) -> str:
        return f"{self.__class__!s}({self.__dict__!r})"

    @classmethod
    def from_dict(cls, definitions: dict[str, Any]) -> Self:
        result: dict[str, DefinedType] = {}
        for k, v in definitions.items():
            result[k] = Structure.from_named_dict(k, v)

        return cls(result)
