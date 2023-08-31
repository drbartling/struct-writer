from structured_api import Structure


def test_structure_generation():
    test_struct = {
        "my_struct": {
            "brief": "My structure",
            "description": "An example structure",
            "members": {
                "temperature_c": "int16",
            },
        }
    }

    s = Structure.from_dict(test_struct)
    result = s.render()

    expected = (
        "/** My structure\n"
        "*\n"
        "* An example structure\n"
        "*/\n"
        "typedef struct my_struct_s {\n"
        "int16_t temperature_c;\n"
        "} my_struct_t;\n"
    )
    assert expected == result
