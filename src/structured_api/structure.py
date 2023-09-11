from typing import Any, Optional

from pydantic.dataclasses import dataclass


@dataclass
class Structure:
    name: str
    brief: Optional[str] = None
    description: Optional[str] = None
    members: Optional[list["StructureMember"]] = None

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]):
        name = list(dictionary.keys())[0]
        dictionary[name]["name"] = name
        dictionary[name]["members"] = StructureMember.from_dict(
            dictionary[name].get("members", {})
        )
        return cls(**dictionary[name])

    def render(self):
        start = (
            "/**\n"
            f"* @brief {self.brief}\n"
            "*\n"
            f"* {self.description}\n"
            "*/\n"
            f"typedef PACKED_STRUCT({self.name}_s) {{\n"
        )
        if self.members:
            members = "\n".join([m.render() for m in self.members])
        else:
            members = "/// Intentionally empty structure\nuint8_t empty[0];"
        end = f"\n}} {self.name}_t;\n\n"
        return start + members + end


@dataclass
class StructureMember:
    name: str
    length: int
    type: str
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]):
        members = []
        for name, definition in dictionary.items():
            definition["name"] = name
            members.append(cls(**definition))
        return members

    def render(self):
        s = f"/// {self.description}\n" if self.description is not None else ""
        if "int" == self.type:
            bits = self.length * 8
            return s + f"int{bits}_t {self.name};"
        if "uint" == self.type:
            bits = self.length * 8
            return s + f"uint{bits}_t {self.name};"
        if "bytes" == self.type:
            return s + f"uint8_t {self.name}[{self.length}];"
        if "void" == self.type:
            return s + f"void * {self.name};"
        return s + f"{self.type}_t {self.name};"
