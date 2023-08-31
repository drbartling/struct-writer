from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Structure:
    name: str
    brief: Optional[str] = None
    description: Optional[str] = None
    members: Optional["Member"] = None

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]):
        name = list(dictionary.keys())[0]
        return cls(
            name=name,
            brief=dictionary[name].get("brief"),
            description=dictionary[name].get("description"),
            members=Member.from_dict(dictionary[name].get("members", {})),
        )

    def render(self):
        start = (
            f"/** {self.brief}\n"
            "*\n"
            f"* {self.description}\n"
            "*/\n"
            f"typedef struct {self.name}_s {{\n"
        )
        if self.members:
            members = "\n".join([m.render() for m in self.members])
        else:
            members = "uint8_t empty[0];"
        end = f"\n}} {self.name}_t;\n"
        return start + members + end


@dataclass
class Member:
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
        if "int" == self.type:
            bits = self.length * 8
            return f"int{bits}_t {self.name};"
        return f"{self.type}_t {self.name};"
