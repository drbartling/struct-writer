import pytest

from structured_api import Structure
from structured_api.structure import StructureMember


def test_structure_generation():
    test_struct = {
        "my_struct": {
            "brief": "My structure",
            "description": "An example structure",
            "members": {
                "temperature": {"length": 2, "type": "int"},
                "units": {"length": 1, "type": "temperature_units"},
            },
        }
    }

    s = Structure.from_dict(test_struct)
    result = s.render()

    expected = (
        "/**\n"
        "* @brief My structure\n"
        "*\n"
        "* An example structure\n"
        "*/\n"
        "typedef PACKED_STRUCT(my_struct_s) {\n"
        "int16_t temperature;\n"
        "temperature_units_t units;\n"
        "} my_struct_t;\n"
        "\n"
    )
    assert expected == result


def test_empty_structure_generation():
    test_struct = {
        "my_struct": {
            "brief": "My structure",
            "description": "An example structure",
        }
    }

    s = Structure.from_dict(test_struct)
    result = s.render()

    expected = (
        "/**\n"
        "* @brief My structure\n"
        "*\n"
        "* An example structure\n"
        "*/\n"
        "typedef PACKED_STRUCT(my_struct_s) {\n"
        "/// Intentionally empty structure\n"
        "uint8_t empty[0];\n"
        "} my_struct_t;\n"
        "\n"
    )
    assert expected == result


def test_structure_member_from_dict_creates_list_of_members():
    member_dict = {
        "temperature": {"length": 2, "type": "int"},
        "foo": {"length": 2, "type": "int"},
    }
    members = StructureMember.from_dict(member_dict)
    assert [
        StructureMember(name="temperature", length=2, type="int"),
        StructureMember(name="foo", length=2, type="int"),
    ] == members


structure_member_rendering_params = [
    ({"temperature": {"length": 2, "type": "int"}}, "int16_t temperature;"),
    ({"foo": {"length": 2, "type": "int"}}, "int16_t foo;"),
    ({"temperature": {"length": 4, "type": "int"}}, "int32_t temperature;"),
    ({"temperature": {"length": 2, "type": "uint"}}, "uint16_t temperature;"),
    ({"foo": {"length": 42, "type": "bytes"}}, "uint8_t foo[42];"),
    ({"foo": {"length": 2, "type": "void"}}, "void * foo;"),
    ({"foo": {"length": 2, "type": "my_type"}}, "my_type_t foo;"),
]


@pytest.mark.parametrize(
    "member_dict, expected", structure_member_rendering_params
)
def test_structure_member_rendering(member_dict, expected):
    members = StructureMember.from_dict(member_dict)
    member = members[0]
    result = member.render()
    assert expected == result
