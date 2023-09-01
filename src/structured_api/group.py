from typing import Any, Optional

from pydantic.dataclasses import dataclass


@dataclass
class Group:
    name: str
    members: dict[int, "GroupMember"]
    brief: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        for member in self.members.values():
            member.group = self

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]):
        name = list(dictionary.keys())[0]
        return cls(
            name=name,
            members=GroupMember.from_dict(dictionary[name].get("members", {})),
            brief=dictionary[name].get("brief"),
            description=dictionary[name].get("description"),
        )

    def render(self):
        return self.render_enum() + "\n" + self.render_union()

    def render_enum(self):
        start = (
            f"/** {self.name} group tags\n"
            "*\n"
            f"* Tags to identify which structure to parse when handling the {self.name} group\n"
            "*/\n"
            f"typedef enum {self.name}_tag_e {{\n"
        )
        members = "\n".join([m.render_enum() for m in self.members.values()])
        end = f"\n}} {self.name}_tag_t;\n"
        return start + members + end

    def render_union(self):
        start = (
            f"/** {self.brief}\n"
            "*\n"
            f"* {self.description}\n"
            "*/\n"
            f"typedef struct {self.name}_s {{\n"
            f"{self.name}_tag_t tag;\n"
            f"union {{\n"
        )
        members = "\n".join([m.render_union() for m in self.members.values()])
        end = f"\n}} {self.name};\n" f"}} {self.name}_t;\n"
        return start + members + end


@dataclass
class GroupMember:
    name: str
    tag: int
    length: int
    type: str
    description: str = ""
    group: Optional[Group] = None

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]):
        members = {}
        for name, definition in dictionary.items():
            definition["name"] = name
            assert definition["tag"] not in members
            members[definition["tag"]] = cls(**definition)
        return members

    def render_enum(self):
        s = (
            f"/// {self.description}\n"
            f"/// @see {self.type}_t\n"
            f"{self.group.name}_{self.name} = 0x{self.tag:0X},"
        )
        return s

    def render_union(self):
        return f"{self.type}_t {self.name};"
