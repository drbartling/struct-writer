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
    result = generate_structured_code.render_definitions(definitions, template)
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


def test_render_empty_struct():
    definitions = {
        "MY_empty_struct": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 0,
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// My struct
/// A struct
typedef struct MY_empty_struct_s{
/// Structure is intentially empty (zero sized)
uint8_t empty[0];
} MY_empty_struct_t;
STATIC_ASSERT_TYPE_SIZE(MY_empty_struct_t, 0);

"""

    assert expected == result


def test_render_struct():
    definitions = {
        "MY_struct": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 1,
            "members": [
                {
                    "name": "foo",
                    "size": 1,
                    "type": "int",
                    "description": "A foo walks into a bar",
                },
            ],
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// My struct
/// A struct
typedef struct MY_struct_s{
/// A foo walks into a bar
int8_t foo;
} MY_struct_t;
STATIC_ASSERT_TYPE_SIZE(MY_struct_t, 1);

"""

    assert expected == result


def test_render_empty_group():
    definitions = {
        "MY_empty_group": {
            "type": "group",
            "display_name": "My group",
            "description": "A group",
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = ""

    assert expected == result


def test_render_group():
    definitions = {
        "MY_group": {
            "type": "group",
            "display_name": "My group",
            "description": "A group",
        },
        "MY_grouped_struct": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 0,
            "groups": {
                "MY_group": {"value": 0, "name": "grouped_struct"},
            },
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// MY_group tag
/// Enumeration for MY_group tag
typedef enum MY_group_tag_e{
/// @see MY_grouped_struct_t
MY_group_tag_grouped_struct = 0x0,
} MY_group_tag_t;
STATIC_ASSERT_TYPE_SIZE(MY_group_tag_t, 1);

/// My struct
/// A struct
typedef struct MY_grouped_struct_s{
/// Structure is intentially empty (zero sized)
uint8_t empty[0];
} MY_grouped_struct_t;
STATIC_ASSERT_TYPE_SIZE(MY_grouped_struct_t, 0);

/// My group
/// A group
typedef struct MY_group_u_s{
/// MY_group tag
MY_group_tag_t tag;
union {
/// A struct
MY_grouped_struct_t grouped_struct;
} value;
} MY_group_u_t;
STATIC_ASSERT_TYPE_SIZE(MY_group_u_t, 1);

"""

    assert expected == result


def test_render_structs_in_dependency_order():
    definitions = {
        "MY_struct1": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 1,
            "members": [
                {
                    "name": "foo",
                    "size": 1,
                    "type": "MY_struct2",
                    "description": "A foo walks into a bar",
                },
            ],
        },
        "MY_struct2": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 1,
            "members": [
                {
                    "name": "bar",
                    "size": 1,
                    "type": "int",
                    "description": "A bar",
                },
            ],
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// My struct
/// A struct
typedef struct MY_struct2_s{
/// A bar
int8_t bar;
} MY_struct2_t;
STATIC_ASSERT_TYPE_SIZE(MY_struct2_t, 1);

/// My struct
/// A struct
typedef struct MY_struct1_s{
/// A foo walks into a bar
MY_struct2_t foo;
} MY_struct1_t;
STATIC_ASSERT_TYPE_SIZE(MY_struct1_t, 1);

"""

    assert expected == result
