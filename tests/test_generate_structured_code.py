from struct_writer import default_template, generate_structured_code


def test_render_enum():
    definitions = {
        "MY_enum": {
            "type": "enum",
            "display_name": "My enum",
            "description": "An enum",
            "size": 1,
            "values": [
                {
                    "value": 0,
                    "label": "first_value",
                    "description": "The first value in this enum",
                },
                {
                    "label": "second_value",
                    "description": "The second value in this enum",
                },
            ],
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_enum(
        "MY_enum", definitions, template
    )
    expected = """\
/// My enum
/// An enum
typedef enum MY_enum_e{
/// The first value in this enum
MY_enum_first_value = 0x0,
/// The second value in this enum
MY_enum_second_value,
} MY_enum_t;
STATIC_ASSERT_TYPE_SIZE(MY_enum_t, 1);

"""

    assert expected == result
