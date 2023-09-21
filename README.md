# Structured API

Define a bare structured API, useful for interfaces that don't need to be
portable across multiple platforms.  E.G. embedded applications targeting a
single architecture.

## Usage

Define the API in TOML or another markup language.

```toml
prefix="API"

[command]
type="group"
display_name="API command"
description="Commands sent from the host to the device"

[cmd_reset]
type="struct"
group=command
group_enum=1
display_name="reset request"
description="Request a software reset"

[cmd_temperature_set]
type="struct"
group=command
group_enum=2
display_name="Request temperature change (C)"
description="Request a change in temperature in degrees C"
[cmd_temperature_set.members]
temperature_c = "int16"
```

This will generate code that looks like this for c by default
```c
/// API command tags
///
/// Enumerates the Commands sent from the host to the device
typedef enum API_command_tag_e {
	/// Request a software reset
	/// @see API_cmd_reset_t
	API_rsp_reset = 0x1,
	/// Request temperature change (C)
	/// @see API_cmd_temperature_set_t
	API_cmd_temperature_set = 0x2,
} API_command_tag_t

/// reset request
///
/// Request a software reset
typedef struct API_rsp_reset_e {
    uint8_t empty[0];
} API_rsp_reset_t;

/// Request temperature change (C)
///
/// Request a change in temperature in degrees C
typedef struct API_cmd_temperature_set_e {
    int16_t temperature_c;
} API_cmd_temperature_set_t;

typedef struct  API_command_s {
	API_command_tag_t tag;
	union {
		API_cmd_reset_t reset;
		API_cmd_temperature_set_t cmd_temperature_set;
	} command;
} API_command_t;
```

## development
```
watchexec.exe --clear --restart  --debounce 500 --exts py,toml "isort . && black . && pytest && generate-code --input-definition examples/structures.toml --template-file examples/template.toml --output-file examples/output/structures.h && pylint ."
```
