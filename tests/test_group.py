from structured_api.group import Group


def test_simple_group():
    test_group = {
        "commands": {
            "brief": "Thermostat commands",
            "description": "Commands sent to thermostat over debug port",
            "members": {
                "reset": {"tag": 1, "length": 0, "type": "reset"},
                "set_temperature": {
                    "tag": 2,
                    "length": 3,
                    "type": "set_temperature",
                },
            },
        }
    }

    s = Group.from_dict(test_group)
    result = s.render()

    expected = (
        "/** commands group tags\n"
        "*\n"
        "* Tags to identify which structure to parse when handling the commands group\n"
        "*/\n"
        "typedef enum commands_tag_e {\n"
        "/// \n"
        "/// @see reset_t\n"
        "commands_reset = 0x1,\n"
        "/// \n"
        "/// @see set_temperature_t\n"
        "commands_set_temperature = 0x2,\n"
        "} commands_tag_t;\n"
        "\n"
        "/** Thermostat commands\n"
        "*\n"
        "* Commands sent to thermostat over debug port\n"
        "*/\n"
        "typedef struct commands_s {\n"
        "commands_tag_t tag;\n"
        "union {\n"
        "reset_t reset;\n"
        "set_temperature_t set_temperature;\n"
        "} commands;\n"
        "} commands_t;\n"
    )

    assert expected == result
