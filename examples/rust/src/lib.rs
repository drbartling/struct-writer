include!(concat!(env!("OUT_DIR"), "/example_structs.rs"));

#[cfg(test)]
mod tests {
    use super::*;
    use pretty_assertions::assert_eq;
    use rstest::rstest;

    #[rstest]
    #[case(commands::reset(cmd_reset{}), [1, 0, 0, 0, 0, 0])]
    fn test_something(#[case] input: commands, #[case] expected: commands_slice) {
        let result: commands_slice = input.clone().into();
        assert_eq!(result, expected);

        let back_to_command: commands = result.try_into().unwrap();
        assert_eq!(back_to_command, input);
    }

    #[rstest]
    fn test_serialize_bitfields() {
        let state = hvac_state {
            fan_enabled: true,
            ac_enabled: true,
            heat_enabled: false,
            units: temperature_units::f,
        };
        let result = format!("{}", serde_json::to_string(&state).unwrap());
        let expected =
            "{\"fan_enabled\":true,\"ac_enabled\":true,\"heat_enabled\":false,\"units\":\"f\"}"
                .to_owned();
        assert_eq!(expected, result);
    }
}
