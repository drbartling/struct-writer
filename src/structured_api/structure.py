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
            brief=dictionary[name]["brief"],
            description=dictionary[name]["description"],
            members=Member.from_dict(dictionary[name]["members"]),
        )

    def render(self):
        start = (
            f"/** {self.brief}\n"
            "*\n"
            f"* {self.description}\n"
            "*/\n"
            f"typedef struct {self.name}_s {{\n"
        )
        members = "\n".join([m.render() for m in self.members])
        end = f"\n}} {self.name}_t;\n"
        return start + members + end


@dataclass
class Member:
    name: str
    type: str
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]):
        return [cls(n, t) for n, t in dictionary.items()]

    def render(self):
        return f"{self.type}_t {self.name};"
