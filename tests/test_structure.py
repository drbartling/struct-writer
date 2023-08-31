from structured_api import Structure


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
        "/** My structure\n"
        "*\n"
        "* An example structure\n"
        "*/\n"
        "typedef struct my_struct_s {\n"
        "int16_t temperature;\n"
        "temperature_units_t units;\n"
        "} my_struct_t;\n"
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
        "/** My structure\n"
        "*\n"
        "* An example structure\n"
        "*/\n"
        "typedef struct my_struct_s {\n"
        "uint8_t empty[0];\n"
        "} my_struct_t;\n"
    )
    assert expected == result
