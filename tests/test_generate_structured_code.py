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
/// Structure is intentionally empty (zero sized)
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
            "size": 1,
        },
        "MY_grouped_int": {
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
            "groups": {
                "MY_group": {"value": 0, "name": "grouped_int"},
            },
        },
        "MY_grouped_uint": {
            "type": "structure",
            "display_name": "My struct",
            "description": "A struct",
            "size": 1,
            "members": [
                {
                    "name": "bar",
                    "size": 1,
                    "type": "uint",
                    "description": "A bar walks into a foo",
                },
            ],
            "groups": {
                "MY_group": {"value": 1, "name": "grouped_uint"},
            },
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// MY_group tag
/// Enumeration for MY_group tag
typedef enum MY_group_tag_e{
/// @see MY_grouped_int_t
MY_group_tag_grouped_int = 0x0,
/// @see MY_grouped_uint_t
MY_group_tag_grouped_uint = 0x1,
} MY_group_tag_t;
STATIC_ASSERT_TYPE_SIZE(MY_group_tag_t, 1);

/// My struct
/// A struct
typedef struct MY_grouped_int_s{
/// A foo walks into a bar
int8_t foo;
} MY_grouped_int_t;
STATIC_ASSERT_TYPE_SIZE(MY_grouped_int_t, 1);

/// My struct
/// A struct
typedef struct MY_grouped_uint_s{
/// A bar walks into a foo
uint8_t bar;
} MY_grouped_uint_t;
STATIC_ASSERT_TYPE_SIZE(MY_grouped_uint_t, 1);

/// My group
/// A group
typedef union MY_group_union_u{
/// A struct
MY_grouped_int_t grouped_int;
/// A struct
MY_grouped_uint_t grouped_uint;
} MY_group_union_t;
STATIC_ASSERT_TYPE_SIZE(MY_group_union_t, 1);

/// My group
/// A group
typedef struct MY_group_s{
/// MY_group tag
MY_group_tag_t tag;
/// Union of group structures
MY_group_union_t value;
} MY_group_t;
STATIC_ASSERT_TYPE_SIZE(MY_group_t, 2);

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


def test_render_bit_field():
    definitions = {
        "MY_field": {
            "type": "bit_field",
            "display_name": "My field",
            "description": "A bit field",
            "size": 1,
            "members": [
                {
                    "name": "foo",
                    "start": 1,
                    "last": 3,
                    "bits": 3,
                    "type": "int",
                    "description": "foo",
                },
                {
                    "name": "bar",
                    "start": 4,
                    "bits": 1,
                    "type": "uint",
                    "description": "bar",
                },
                {
                    "name": "baz",
                    "start": 6,
                    "type": "uint",
                    "description": "baz",
                },
                {
                    "name": "bazz",
                    "start": 7,
                    "last": 7,
                    "type": "uint",
                    "description": "bazz",
                },
            ],
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// My field
/// A bit field
typedef struct MY_field_s{
uint8_t reserved_0:1;
/// foo
int8_t foo:3;
/// bar
uint8_t bar:1;
uint8_t reserved_5:1;
/// baz
uint8_t baz:1;
/// bazz
uint8_t bazz:1;
} MY_field_t;
STATIC_ASSERT_TYPE_SIZE(MY_field_t, 1);

"""
    assert expected == result


def test_render_bit_field_with_enum():
    definitions = {
        "MY_field2": {
            "type": "bit_field",
            "display_name": "My field",
            "description": "A bit field",
            "size": 2,
            "members": [
                {
                    "name": "power",
                    "start": 2,
                    "bits": 1,
                    "type": "MY_power",
                    "description": "Power",
                }
            ],
        },
        "MY_power": {
            "type": "enum",
            "display_name": "Power",
            "description": "Power state",
            "size": 1,
            "values": [
                {
                    "value": 0,
                    "label": "off",
                    "description": "The power is off",
                },
                {
                    "value": 1,
                    "label": "on",
                    "description": "The power is on",
                },
            ],
        },
    }
    template = default_template.default_template()
    result = generate_structured_code.render_definitions(definitions, template)
    expected = """\
/// Power
/// Power state
typedef enum MY_power_e{
/// The power is off
MY_power_off = 0x0,
/// The power is on
MY_power_on = 0x1,
} MY_power_t;
STATIC_ASSERT_TYPE_SIZE(MY_power_t, 1);

/// My field
/// A bit field
typedef struct MY_field2_s{
uint16_t reserved_0:2;
/// Power
MY_power_t power:1;
} MY_field2_t;
STATIC_ASSERT_TYPE_SIZE(MY_field2_t, 2);

"""
    assert expected == result
