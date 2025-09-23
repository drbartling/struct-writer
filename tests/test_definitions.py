from typing import Any

import pytest
from devtools import debug

from struct_writer.definitions import (
    ParseFailed,
    Structure,
    StructureMember,
    TypeDefinitions,
)

structure_params = [
    (
        "Empty Structure",
        {
            "empty_struct": {
                "description": "An empty structure",
                "display_name": "Empty Structure",
                "size": 0,
            }
        },
        Structure(
            name="empty_struct",
            display_name="Empty Structure",
            description="An empty structure",
            size=0,
            members=[],
        ),
    ),
    (
        "Simple Structure",
        {
            "simple_struct": {
                "description": "A simple structure",
                "display_name": "Simple Structure",
                "size": 1,
                "members": [
                    {
                        "name": "number",
                        "size": 1,
                        "type": "int",
                        "description": "A small number",
                    },
                ],
            }
        },
        Structure(
            name="simple_struct",
            display_name="Simple Structure",
            description="A simple structure",
            size=1,
            members=[
                StructureMember(
                    name="number",
                    size=1,
                    type="int",
                    description="A small number",
                )
            ],
        ),
    ),
]


@pytest.mark.parametrize(
    ("test_name", "structure_dict", "expected"), structure_params
)
def test_structure(
    test_name: str, structure_dict: dict[str, Any], expected: Structure
) -> None:
    debug(test_name)
    result = Structure.from_dict(structure_dict)
    debug(result)
    debug(expected)
    assert expected == result


def test_mismatch_structure_size() -> None:
    struct = {
        "simple_struct": {
            "description": "A simple structure",
            "display_name": "Simple Structure",
            "size": 0,
            "type": "structure",
            "members": [
                {
                    "name": "number",
                    "size": 1,
                    "type": "int",
                    "description": "A small number",
                },
            ],
        }
    }
    with pytest.raises(ParseFailed):
        _ = Structure.from_dict(struct)


type_definitions_params = [
    (
        "Empty Structure",
        {
            "empty_struct": {
                "description": "An empty structure",
                "display_name": "Empty Structure",
                "size": 0,
            }
        },
        TypeDefinitions(
            {
                "empty_struct": Structure(
                    name="empty_struct",
                    display_name="Empty Structure",
                    description="An empty structure",
                    size=0,
                    members=[],
                ),
            }
        ),
    ),
    (
        "Simple Structure",
        {
            "simple_struct": {
                "description": "A simple structure",
                "display_name": "Simple Structure",
                "size": 1,
                "members": [
                    {
                        "name": "number",
                        "size": 1,
                        "type": "int",
                        "description": "A small number",
                    },
                ],
            }
        },
        TypeDefinitions(
            {
                "simple_struct": Structure(
                    name="simple_struct",
                    display_name="Simple Structure",
                    description="A simple structure",
                    size=1,
                    members=[
                        StructureMember(
                            name="number",
                            size=1,
                            type="int",
                            description="A small number",
                        )
                    ],
                )
            }
        ),
    ),
]


@pytest.mark.parametrize(
    ("test_name", "definition_dict", "expected"), type_definitions_params
)
def test_type_definitions(
    test_name: str, definition_dict: dict[str, Any], expected: TypeDefinitions
) -> None:
    debug(test_name)
    result = TypeDefinitions.from_dict(definition_dict)
    debug(result)
    debug(expected)
    assert expected == result
