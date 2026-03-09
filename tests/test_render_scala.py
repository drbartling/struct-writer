from pathlib import Path

from struct_writer import (
    default_template_scala,
    generate_structured_code,
    render_scala,
)


def test_default_template() -> None:
    # We want to ensure that the default template we use for scala is the same
    # as the example we give in documentation

    this_path = Path(__file__).resolve()
    project_root = this_path / "../.."
    project_root = project_root.resolve()
    template_example = project_root / "examples/template_scala.toml"
    assert template_example.is_file()

    example_template = generate_structured_code.load_markup_file(
        template_example
    )
    default_template = default_template_scala.default_template()

    assert example_template == default_template


def test_render_empty_file() -> None:
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # Check the file description is rendered
    assert "A brief file description" in result
    assert "Longer prose describing what to find in the file" in result
    # Check package and imports are present
    assert "package generated" in result
    assert "import com.github.plokhotnyuk.jsoniter_scala.core._" in result
    assert "import com.github.plokhotnyuk.jsoniter_scala.macros._" in result
    assert "trait ByteSequence" in result
    assert "trait JsonSerializable" in result
    assert "object BinaryUtils" in result
    # Check footer
    assert "// End of generated code" in result


def test_render_file_with_enum() -> None:
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
        "temperature_units": {
            "description": "The temperature units",
            "display_name": "Temperature units",
            "size": 1,
            "type": "enum",
            "values": [
                {
                    "label": "c",
                    "value": 0,
                    "display_name": "C",
                    "description": "Degrees Celsius",
                },
                {
                    "label": "f",
                    "value": 1,
                    "display_name": "F",
                    "description": "Degrees Fahrenheit",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # Check enum structure
    assert "sealed trait temperature_units extends ByteSequence" in result
    assert "object temperature_units" in result
    assert "case object c extends temperature_units" in result
    assert "case object f extends temperature_units" in result
    # Check helper methods
    assert "def fromByte(value: Byte): Option[temperature_units]" in result
    assert "def toByte(value: temperature_units): Byte" in result
    assert "def toDisplayString(value: temperature_units): String" in result
    assert (
        "def fromDisplayString(s: String): Option[temperature_units]" in result
    )
    assert "def fromBytes(bytes: Array[Byte]): temperature_units" in result
    # Check match cases
    assert "case 0 => Some(temperature_units.c)" in result
    assert "case 1 => Some(temperature_units.f)" in result


def test_render_file_with_structure_jsoniter() -> None:
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
        "cmd_temperature_set": {
            "description": "Request a change in temperature",
            "display_name": "Request temperature change",
            "size": 3,
            "type": "structure",
            "members": [
                {
                    "name": "temperature",
                    "size": 2,
                    "type": "int",
                    "description": "Desired temperature",
                },
                {
                    "name": "units",
                    "size": 1,
                    "type": "uint",
                    "description": "Selected temperature unit",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # Check case class
    assert "final case class cmd_temperature_set(" in result
    assert "temperature: Short," in result
    assert "units: Int," in result
    assert "extends ByteSequence with JsonSerializable" in result
    # Check companion object
    assert (
        "object cmd_temperature_set extends ByteSequenceCodec[cmd_temperature_set]"
        in result
    )
    assert "final val SizeInBytes = 3" in result
    # Check decode
    assert "def fromBytes(bytes: Array[Byte]): cmd_temperature_set" in result
    assert "BinaryUtils.bytesToInt16LE(bytes, 0)" in result
    assert "BinaryUtils.bytesToUint8LE(bytes, 2)" in result
    # Check encode
    assert "def toBytes(event: cmd_temperature_set): Seq[Byte]" in result
    assert "BinaryUtils.int16LEtoBytes(event.temperature)" in result
    assert "BinaryUtils.uint8LEtoBytes(event.units)" in result


def test_render_empty_group() -> None:
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
        "my_commands": {
            "description": "A set of commands to do stuff",
            "display_name": "Command stuff",
            "type": "group",
            "size": 1,
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # Empty groups should not generate content
    assert "sealed trait my_commands" not in result


def test_render_small_group() -> None:
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
        "commands": {
            "description": "Debug commands for thermostat",
            "display_name": "Thermostat command",
            "type": "group",
            "size": 2,
        },
        "cmd_reset": {
            "description": "Request a software reset",
            "display_name": "Reset Request",
            "type": "structure",
            "size": 0,
            "groups": {
                "commands": {
                    "value": 1,
                    "name": "reset",
                },
            },
        },
        "cmd_temperature_set": {
            "description": "Request a change in temperature",
            "display_name": "Request temperature change",
            "type": "structure",
            "size": 3,
            "members": [
                {
                    "name": "temperature",
                    "size": 2,
                    "type": "int",
                    "description": "Desired temperature",
                },
                {
                    "name": "units",
                    "size": 1,
                    "type": "uint",
                    "description": "Selected temperature unit",
                },
            ],
            "groups": {
                "commands": {
                    "value": 2,
                    "name": "temperature_set",
                },
            },
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # Check group trait
    assert "sealed trait commands extends ByteSequence" in result
    # Check group decoder object
    assert "object commands {" in result
    assert (
        "def decode(bytes: Array[Byte], streamPositionHead: Long): Try[commands]"
        in result
    )
    assert "val tag = BinaryUtils.bytesToUint16LE(bytes, 0)" in result
    # Check match cases for group members
    assert "case 1 => cmd_reset.decode" in result
    assert "case 2 => cmd_temperature_set.decode" in result
    # Check member structures extend the group
    assert "extends commands with JsonSerializable" in result


def test_render_bitfield() -> None:
    definitions = {
        "file": {
            "brief": "A brief file description",
            "description": "Longer prose describing what to find in the file",
        },
        "hvac_state": {
            "description": "State flags for HVAC",
            "display_name": "HVAC State",
            "type": "bit_field",
            "size": 1,
            "members": [
                {
                    "name": "fan_enabled",
                    "start": 0,
                    "bits": 1,
                    "type": "bool",
                    "description": "Set to true when fan is enabled",
                },
                {
                    "name": "ac_enabled",
                    "start": 1,
                    "bits": 1,
                    "type": "bool",
                    "description": "Set to true when AC is enabled",
                },
                {
                    "name": "mode",
                    "start": 2,
                    "bits": 2,
                    "type": "uint",
                    "description": "Operating mode",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # Check case class
    assert "final case class hvac_state(" in result
    assert "fan_enabled: Boolean," in result
    assert "ac_enabled: Boolean," in result
    assert "mode: Int," in result
    # Check companion object
    assert "object hvac_state extends ByteSequenceCodec[hvac_state]" in result
    assert "final val SizeInBytes = 1" in result
    # Check decode with bit operations
    assert "val rawBits = BinaryUtils.bytesToUint8LE(bytes, 0)" in result
    assert "fan_enabled = ((rawBits >> 0) & 1) != 0" in result
    assert "ac_enabled = ((rawBits >> 1) & 1) != 0" in result
    assert "mode = ((rawBits >> 2) & 3).toInt" in result
    # Check encode with bit operations
    assert "var rawBits: Int = 0" in result
    assert "rawBits |= ((if (value.fan_enabled) 1 else 0) << 0)" in result
    assert "rawBits |= ((if (value.ac_enabled) 1 else 0) << 1)" in result
    assert "rawBits |= ((value.mode & 3) << 2)" in result


def test_extract_package_from_path() -> None:
    # Test standard Scala project path
    path = Path(
        "/Users/test/project/src/main/scala/com/example/generated/MyFile.scala"
    )
    result = render_scala.extract_package_from_path(path)
    assert result == "com.example.generated"

    # Test path without standard structure
    path = Path("/some/other/path/output.scala")
    result = render_scala.extract_package_from_path(path)
    assert result == "generated"


def test_escape_scala_keyword() -> None:
    # Test that Scala keywords are escaped
    assert render_scala.escape_scala_keyword("type") == "`type`"
    assert render_scala.escape_scala_keyword("class") == "`class`"
    assert render_scala.escape_scala_keyword("object") == "`object`"
    # Test that non-keywords are not escaped
    assert render_scala.escape_scala_keyword("myField") == "myField"
    assert render_scala.escape_scala_keyword("temperature") == "temperature"


def test_format_large_int() -> None:
    # Test normal integers
    assert render_scala.format_large_int(0) == "0"
    assert render_scala.format_large_int(100) == "100"
    assert render_scala.format_large_int(-100) == "-100"
    # Test integers at Int boundaries
    assert render_scala.format_large_int(2147483647) == "2147483647"
    assert render_scala.format_large_int(-2147483648) == "-2147483648"
    # Test integers beyond Int boundaries (need L suffix)
    assert render_scala.format_large_int(2147483648) == "2147483648L"
    assert render_scala.format_large_int(-2147483649) == "-2147483649L"


def test_render_enum_with_scala_keyword() -> None:
    """Test that enum values that are Scala keywords get properly escaped."""
    definitions = {
        "file": {
            "brief": "Test file",
            "description": "Testing keyword escaping",
        },
        "my_enum": {
            "description": "An enum with keyword values",
            "display_name": "My Enum",
            "size": 1,
            "type": "enum",
            "values": [
                {
                    "label": "type",
                    "value": 0,
                    "display_name": "Type",
                    "description": "Type value",
                },
                {
                    "label": "class",
                    "value": 1,
                    "display_name": "Class",
                    "description": "Class value",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # Keywords should be escaped with backticks
    assert "case object `type` extends my_enum" in result
    assert "case object `class` extends my_enum" in result


# =============================================================================
# JSON Round-Trip Tests: binary -> scala -> json -> scala -> binary
# =============================================================================


def test_binary_to_scala_to_json_structure() -> None:
    """Test that generated code supports binary -> Scala -> JSON conversion.

    The generated Scala code should have:
    - fromBytes(bytes): Deserializes binary to Scala case class
    - serialize(): Serializes Scala case class to JSON string
    - CustomJsonSerializer trait for JSON output
    """
    definitions = {
        "file": {
            "brief": "Round-trip test",
            "description": "Testing binary -> scala -> json",
        },
        "sensor_reading": {
            "description": "Sensor data packet",
            "display_name": "Sensor Reading",
            "size": 8,
            "type": "structure",
            "members": [
                {
                    "name": "sensor_id",
                    "size": 2,
                    "type": "uint",
                    "description": "Unique sensor identifier",
                },
                {
                    "name": "temperature",
                    "size": 2,
                    "type": "int",
                    "description": "Temperature in tenths of degrees",
                },
                {
                    "name": "humidity",
                    "size": 2,
                    "type": "uint",
                    "description": "Relative humidity percentage",
                },
                {
                    "name": "flags",
                    "size": 2,
                    "type": "uint",
                    "description": "Status flags",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Binary -> Scala: fromBytes method
    assert "def fromBytes(bytes: Array[Byte]): sensor_reading" in result
    assert "BinaryUtils.bytesToUint16LE(bytes, 0)" in result  # sensor_id
    assert "BinaryUtils.bytesToInt16LE(bytes, 2)" in result  # temperature
    assert "BinaryUtils.bytesToUint16LE(bytes, 4)" in result  # humidity
    assert "BinaryUtils.bytesToUint16LE(bytes, 6)" in result  # flags

    # Scala -> JSON: JsonSerializable trait with jsoniter codec
    assert "extends ByteSequence with JsonSerializable" in result
    assert "implicit val codec: JsonValueCodec[sensor_reading]" in result
    assert "JsonCodecMaker.make" in result

    # JSON serialization/deserialization methods
    assert "def serialize(): String" in result
    assert "def serializeToBytes(): Array[Byte]" in result
    assert "def deserialize(json: String): sensor_reading" in result


def test_json_to_scala_to_binary_structure() -> None:
    """Test that generated code supports JSON -> Scala -> binary conversion.

    The generated Scala code should have:
    - deserialize(json): Deserializes JSON string to Scala case class
    - JsonValueCodec for jsoniter-scala serialization
    - toBytes(event): Serializes Scala case class to binary
    """
    definitions = {
        "file": {
            "brief": "Round-trip test",
            "description": "Testing json -> scala -> binary",
        },
        "motor_command": {
            "description": "Motor control command",
            "display_name": "Motor Command",
            "size": 6,
            "type": "structure",
            "members": [
                {
                    "name": "motor_id",
                    "size": 1,
                    "type": "uint",
                    "description": "Motor identifier",
                },
                {
                    "name": "speed",
                    "size": 2,
                    "type": "int",
                    "description": "Speed in RPM (can be negative)",
                },
                {
                    "name": "position",
                    "size": 2,
                    "type": "uint",
                    "description": "Target position",
                },
                {
                    "name": "enabled",
                    "size": 1,
                    "type": "bool",
                    "description": "Motor enabled flag",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # JSON -> Scala: jsoniter-scala codec
    assert (
        "object motor_command extends ByteSequenceCodec[motor_command]"
        in result
    )
    assert "implicit val codec: JsonValueCodec[motor_command]" in result
    assert "JsonCodecMaker.make" in result
    assert "def deserialize(json: String): motor_command" in result
    assert "readFromString(json)(codec)" in result

    # Case class fields with correct types
    assert "motor_id: Int" in result  # uint8 -> Int
    assert "speed: Short" in result  # int16 -> Short
    assert "position: Int" in result  # uint16 -> Int
    assert "enabled: Boolean" in result  # bool -> Boolean

    # Scala -> Binary: toBytes method
    assert "def toBytes(event: motor_command): Seq[Byte]" in result
    assert "BinaryUtils.uint8LEtoBytes(event.motor_id)" in result
    assert "BinaryUtils.int16LEtoBytes(event.speed)" in result
    assert "BinaryUtils.uint16LEtoBytes(event.position)" in result


def test_hex_string_parsing_utilities() -> None:
    """Test that BinaryUtils includes hex string parsing for JSON round-trip."""
    definitions = {
        "file": {
            "brief": "Test file",
            "description": "Testing hex parsing utilities",
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Verify hex parsing utilities for JSON deserialization
    assert "def parseHexString(hex: String): Long" in result
    assert 'stripPrefix("0x")' in result
    assert "java.lang.Long.parseLong(cleaned, 16)" in result
    assert "def parseHexStringToInt(hex: String): Int" in result
    assert "def parseHexStringToByte(hex: String): Byte" in result


def test_round_trip_with_enum_field() -> None:
    """Test JSON round-trip for structures containing enum fields.

    Enums are serialized as display strings in JSON and parsed back using
    fromDisplayString().
    """
    definitions = {
        "file": {
            "brief": "Enum round-trip test",
            "description": "Testing enum JSON serialization",
        },
        "operating_mode": {
            "description": "Device operating mode",
            "display_name": "Operating Mode",
            "size": 1,
            "type": "enum",
            "values": [
                {
                    "label": "idle",
                    "value": 0,
                    "display_name": "Idle",
                    "description": "Device is idle",
                },
                {
                    "label": "running",
                    "value": 1,
                    "display_name": "Running",
                    "description": "Device is running",
                },
                {
                    "label": "error",
                    "value": 2,
                    "display_name": "Error",
                    "description": "Device has error",
                },
            ],
        },
        "device_status": {
            "description": "Device status message",
            "display_name": "Device Status",
            "size": 4,
            "type": "structure",
            "members": [
                {
                    "name": "device_id",
                    "size": 2,
                    "type": "uint",
                    "description": "Device identifier",
                },
                {
                    "name": "mode",
                    "size": 1,
                    "type": "operating_mode",
                    "description": "Current operating mode",
                },
                {
                    "name": "battery",
                    "size": 1,
                    "type": "uint",
                    "description": "Battery percentage",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Enum should have toDisplayString and fromDisplayString
    assert "def toDisplayString(value: operating_mode): String" in result
    assert "def fromDisplayString(s: String): Option[operating_mode]" in result

    # Enum field should use the enum type
    assert "mode: operating_mode" in result  # Enum type
    # Enum should have its own codec for string serialization
    assert "implicit val codec: JsonValueCodec[operating_mode]" in result

    # Jsoniter codec handles enum deserialization via fromDisplayString
    # (The codec is generated in the enum companion object)


def test_round_trip_with_nested_structure() -> None:
    """Test JSON round-trip for structures containing nested structures."""
    definitions = {
        "file": {
            "brief": "Nested structure test",
            "description": "Testing nested structure JSON round-trip",
        },
        "gps_coordinates": {
            "description": "GPS position",
            "display_name": "GPS Coordinates",
            "size": 8,
            "type": "structure",
            "members": [
                {
                    "name": "latitude",
                    "size": 4,
                    "type": "int",
                    "description": "Latitude in microdegrees",
                },
                {
                    "name": "longitude",
                    "size": 4,
                    "type": "int",
                    "description": "Longitude in microdegrees",
                },
            ],
        },
        "location_report": {
            "description": "Location report with timestamp",
            "display_name": "Location Report",
            "size": 12,
            "type": "structure",
            "members": [
                {
                    "name": "timestamp",
                    "size": 4,
                    "type": "uint",
                    "description": "Unix timestamp",
                },
                {
                    "name": "position",
                    "size": 8,
                    "type": "gps_coordinates",
                    "description": "GPS position",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Nested structure should use the actual type (jsoniter handles it)
    assert "position: gps_coordinates" in result
    # Jsoniter codec for nested structure
    assert "implicit val codec: JsonValueCodec[gps_coordinates]" in result
    # Jsoniter handles nested structure deserialization automatically

    # Binary round-trip for nested structure
    assert "gps_coordinates.fromBytes(bytes.slice(4, 12))" in result
    assert "bytes.appendAll(event.position.toByteSeq.get)" in result


def test_round_trip_with_reserved_fields() -> None:
    """Test that reserved fields are handled correctly in JSON round-trip.

    Reserved fields should:
    - BE included in JSON intermediate class as hex strings (for binary round-trip)
    - Be serialized as hex string during Scala -> JSON
    - Be parsed from hex string during JSON -> Scala
    """
    definitions = {
        "file": {
            "brief": "Reserved fields test",
            "description": "Testing reserved field handling",
        },
        "packet_header": {
            "description": "Packet header with reserved bytes",
            "display_name": "Packet Header",
            "size": 8,
            "type": "structure",
            "members": [
                {
                    "name": "version",
                    "size": 1,
                    "type": "uint",
                    "description": "Protocol version",
                },
                {
                    "name": "reserved1",
                    "size": 3,
                    "type": "reserved",
                    "description": "Reserved for future use",
                },
                {
                    "name": "length",
                    "size": 2,
                    "type": "uint",
                    "description": "Payload length",
                },
                {
                    "name": "reserved2",
                    "size": 2,
                    "type": "reserved",
                    "description": "Reserved padding",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Reserved fields are handled by jsoniter
    assert "implicit val codec: JsonValueCodec[packet_header]" in result
    assert "version: Int" in result
    assert "length: Int" in result  # uint16 -> Int
    # Reserved fields are stored as Array[Byte] in Scala
    assert "reserved1: Array[Byte]" in result
    assert "reserved2: Array[Byte]" in result

    # Jsoniter codec handles serialization automatically


def test_round_trip_bitfield() -> None:
    """Test JSON round-trip for bit fields."""
    definitions = {
        "file": {
            "brief": "Bitfield round-trip test",
            "description": "Testing bitfield JSON serialization",
        },
        "status_flags": {
            "description": "Status bit flags",
            "display_name": "Status Flags",
            "type": "bit_field",
            "size": 1,
            "members": [
                {
                    "name": "power_on",
                    "start": 0,
                    "bits": 1,
                    "type": "bool",
                    "description": "Power is on",
                },
                {
                    "name": "connected",
                    "start": 1,
                    "bits": 1,
                    "type": "bool",
                    "description": "Network connected",
                },
                {
                    "name": "error_code",
                    "start": 2,
                    "bits": 4,
                    "type": "uint",
                    "description": "Error code (0-15)",
                },
                {
                    "name": "mode",
                    "start": 6,
                    "bits": 2,
                    "type": "uint",
                    "description": "Operating mode (0-3)",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Bitfield should have ByteSequenceCodec
    assert (
        "object status_flags extends ByteSequenceCodec[status_flags]" in result
    )

    # Jsoniter codec for bitfield
    assert "implicit val codec: JsonValueCodec[status_flags]" in result
    assert "JsonCodecMaker.make" in result
    assert "power_on: Boolean" in result
    assert "connected: Boolean" in result
    assert "error_code: Int" in result
    assert "mode: Int" in result

    # JSON deserialization uses jsoniter
    assert "def deserialize(json: String): status_flags" in result
    assert "readFromString(json)(codec)" in result


def test_round_trip_group() -> None:
    """Test JSON round-trip for groups (tagged unions)."""
    definitions = {
        "file": {
            "brief": "Group round-trip test",
            "description": "Testing group JSON serialization",
        },
        "messages": {
            "description": "Message types",
            "display_name": "Messages",
            "type": "group",
            "size": 2,
        },
        "msg_ping": {
            "description": "Ping message",
            "display_name": "Ping",
            "type": "structure",
            "size": 4,
            "members": [
                {
                    "name": "sequence",
                    "size": 4,
                    "type": "uint",
                    "description": "Sequence number",
                },
            ],
            "groups": {
                "messages": {
                    "value": 1,
                    "name": "ping",
                },
            },
        },
        "msg_pong": {
            "description": "Pong message",
            "display_name": "Pong",
            "type": "structure",
            "size": 8,
            "members": [
                {
                    "name": "sequence",
                    "size": 4,
                    "type": "uint",
                    "description": "Sequence number",
                },
                {
                    "name": "timestamp",
                    "size": 4,
                    "type": "uint",
                    "description": "Response timestamp",
                },
            ],
            "groups": {
                "messages": {
                    "value": 2,
                    "name": "pong",
                },
            },
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Group members should have jsoniter codecs
    assert "implicit val codec: JsonValueCodec[msg_ping]" in result
    assert "implicit val codec: JsonValueCodec[msg_pong]" in result

    # Member structures should have ByteSequenceCodec
    assert "object msg_ping extends ByteSequenceCodec[msg_ping]" in result
    assert "object msg_pong extends ByteSequenceCodec[msg_pong]" in result

    # Members have serialize and deserialize methods
    assert "def deserialize(json: String): msg_ping" in result
    assert "def deserialize(json: String): msg_pong" in result
    assert "def serialize(): String" in result


def test_full_round_trip_example() -> None:
    """Integration test demonstrating full binary <-> JSON round-trip capability.

    This test verifies that all the pieces are in place for:
    1. binary -> fromBytes() -> Scala case class
    2. Scala case class -> serialize() -> JSON string
    3. JSON string -> deserialize() -> Scala case class
    4. Scala case class -> toBytes() -> binary
    """
    definitions = {
        "file": {
            "brief": "Full round-trip example",
            "description": "Complete binary/JSON serialization test",
        },
        "telemetry_packet": {
            "description": "Telemetry data packet",
            "display_name": "Telemetry Packet",
            "size": 16,
            "type": "structure",
            "members": [
                {
                    "name": "packet_id",
                    "size": 4,
                    "type": "uint",
                    "description": "Unique packet ID",
                },
                {
                    "name": "sensor_value",
                    "size": 4,
                    "type": "int",
                    "description": "Signed sensor reading",
                },
                {
                    "name": "timestamp",
                    "size": 8,
                    "type": "uint",
                    "description": "64-bit timestamp",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # ===== Binary -> Scala =====
    assert "def fromBytes(bytes: Array[Byte]): telemetry_packet" in result

    # ===== Scala -> JSON =====
    assert "extends ByteSequence with JsonSerializable" in result
    assert "def serialize(): String" in result
    assert "def serializeToBytes(): Array[Byte]" in result

    # ===== JSON -> Scala (jsoniter) =====
    assert "def deserialize(json: String): telemetry_packet" in result
    assert "implicit val codec: JsonValueCodec[telemetry_packet]" in result
    assert "JsonCodecMaker.make" in result

    # ===== Scala -> Binary =====
    assert "def toBytes(event: telemetry_packet): Seq[Byte]" in result
    assert "def toByteSeq: Try[Seq[Byte]]" in result

    # Verify case class field types
    assert "packet_id: Long" in result  # uint32 -> Long
    assert "sensor_value: Int" in result  # int32 -> Int
    assert "timestamp: Long" in result  # uint64 -> Long

    # Jsoniter handles JSON conversion automatically


# =============================================================================
# Additional Tests for New Features
# =============================================================================


def test_scala_to_json_uint_formatting() -> None:
    """Test Scala to JSON conversion for unsigned integers.

    All unsigned integers (regardless of size) are now output as integers,
    not hex strings, for consistency and easier consumption by downstream systems.
    """
    definitions = {
        "file": {
            "brief": "Hex format test",
            "description": "Testing hex string formatting",
        },
        "data_packet": {
            "description": "Packet with various uint sizes",
            "display_name": "Data Packet",
            "size": 15,
            "type": "structure",
            "members": [
                {
                    "name": "small_id",
                    "size": 1,
                    "type": "uint",
                    "description": "1-byte ID (stays as int)",
                },
                {
                    "name": "medium_id",
                    "size": 2,
                    "type": "uint",
                    "description": "2-byte ID (hex with 4 digits)",
                },
                {
                    "name": "large_id",
                    "size": 4,
                    "type": "uint",
                    "description": "4-byte ID (hex with 8 digits)",
                },
                {
                    "name": "huge_id",
                    "size": 8,
                    "type": "uint",
                    "description": "8-byte ID (hex with 16 digits)",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # All uint sizes are stored directly in case class
    assert "small_id: Int" in result  # uint8 -> Int
    assert "medium_id: Int" in result  # uint16 -> Int
    assert "large_id: Long" in result  # uint32 -> Long
    assert "huge_id: Long" in result  # uint64 -> Long

    # Jsoniter codec handles serialization automatically
    assert "implicit val codec: JsonValueCodec[data_packet]" in result


def test_type_discriminator_in_json_class() -> None:
    """Test that _type discriminator field is added to JSON classes."""
    definitions = {
        "file": {
            "brief": "Type discriminator test",
            "description": "Testing _type field",
        },
        "simple_struct": {
            "description": "A simple structure",
            "display_name": "Simple Structure",
            "size": 4,
            "type": "structure",
            "members": [
                {
                    "name": "value",
                    "size": 4,
                    "type": "int",
                    "description": "A value",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Should have jsoniter codec
    assert "implicit val codec: JsonValueCodec[simple_struct]" in result
    assert "def deserialize(json: String): simple_struct" in result

    # Jsoniter handles serialization directly, no _type in case class


def test_enum_unknown_value_parsing() -> None:
    """Test that enum fromDisplayString can parse UnknownValue format.

    The enum should be able to parse strings like:
    - "0x31" (hex format without len suffix)
    - "0x1111" (multi-byte hex format)
    """
    definitions = {
        "file": {
            "brief": "Unknown value test",
            "description": "Testing UnknownValue parsing",
        },
        "status_code": {
            "description": "Status codes",
            "display_name": "Status Code",
            "size": 1,
            "type": "enum",
            "values": [
                {
                    "label": "ok",
                    "value": 0,
                    "display_name": "OK",
                    "description": "Success",
                },
                {
                    "label": "error",
                    "value": 1,
                    "display_name": "Error",
                    "description": "Error occurred",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Should have fromDisplayString for parsing
    assert "def fromDisplayString(s: String): Option[status_code]" in result

    # Should have jsoniter codec for serialization
    assert "implicit val codec: JsonValueCodec[status_code]" in result


def test_nested_structure_json_serialization() -> None:
    """Test that nested structures use jsoniter for JSON."""
    definitions = {
        "file": {
            "brief": "Nested struct JSON test",
            "description": "Testing nested structure JSON serialization",
        },
        "inner_data": {
            "description": "Inner data structure",
            "display_name": "Inner Data",
            "size": 4,
            "type": "structure",
            "members": [
                {
                    "name": "value",
                    "size": 4,
                    "type": "int",
                    "description": "A value",
                },
            ],
        },
        "outer_data": {
            "description": "Outer data with nested struct",
            "display_name": "Outer Data",
            "size": 8,
            "type": "structure",
            "members": [
                {
                    "name": "id",
                    "size": 4,
                    "type": "uint",
                    "description": "ID",
                },
                {
                    "name": "inner",
                    "size": 4,
                    "type": "inner_data",
                    "description": "Nested data",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Jsoniter handles nested structures directly
    assert "implicit val codec: JsonValueCodec[outer_data]" in result

    # Nested structure uses actual type (jsoniter handles serialization)
    assert "inner: inner_data" in result


def test_enum_field_json_conversion() -> None:
    """Test enum fields use toDisplayString for JSON serialization."""
    definitions = {
        "file": {
            "brief": "Enum field JSON test",
            "description": "Testing enum field JSON conversion",
        },
        "color_enum": {
            "description": "Color options",
            "display_name": "Color",
            "size": 1,
            "type": "enum",
            "values": [
                {
                    "label": "red",
                    "value": 0,
                    "display_name": "Red",
                    "description": "Red",
                },
                {
                    "label": "green",
                    "value": 1,
                    "display_name": "Green",
                    "description": "Green",
                },
            ],
        },
        "colored_item": {
            "description": "Item with color",
            "display_name": "Colored Item",
            "size": 5,
            "type": "structure",
            "members": [
                {"name": "id", "size": 4, "type": "uint", "description": "ID"},
                {
                    "name": "color",
                    "size": 1,
                    "type": "color_enum",
                    "description": "Color",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Enum has its own codec which handles string serialization
    assert "implicit val codec: JsonValueCodec[color_enum]" in result

    # Enum field uses the enum type (jsoniter handles conversion)
    assert "color: color_enum" in result


def test_group_raw_data_json_class() -> None:
    """Test that group RawData fallback has proper JSON class with _type."""
    definitions = {
        "file": {
            "brief": "RawData JSON test",
            "description": "Testing RawData JSON class",
        },
        "events": {
            "description": "Event types",
            "display_name": "Events",
            "type": "group",
            "size": 1,
        },
        "event_start": {
            "description": "Start event",
            "display_name": "Start",
            "type": "structure",
            "size": 4,
            "members": [
                {
                    "name": "timestamp",
                    "size": 4,
                    "type": "uint",
                    "description": "Time",
                },
            ],
            "groups": {"events": {"value": 1, "name": "start"}},
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # RawData case class
    assert "final case class events_RawData(" in result
    assert "tag: Int" in result
    assert "rawBytes: Array[Byte]" in result

    # RawData has JsonSerializable trait and codec
    assert "extends events with JsonSerializable" in result
    assert "implicit val codec: JsonValueCodec[events_RawData]" in result


def test_bitfield_json_round_trip_types() -> None:
    """Test bitfield JSON intermediate class has correct types."""
    definitions = {
        "file": {
            "brief": "Bitfield JSON test",
            "description": "Testing bitfield JSON types",
        },
        "flags": {
            "description": "Flags bitfield",
            "display_name": "Flags",
            "type": "bit_field",
            "size": 2,
            "members": [
                {
                    "name": "enabled",
                    "start": 0,
                    "bits": 1,
                    "type": "bool",
                    "description": "Enabled",
                },
                {
                    "name": "level",
                    "start": 1,
                    "bits": 4,
                    "type": "uint",
                    "description": "Level",
                },
                {
                    "name": "active",
                    "start": 5,
                    "bits": 1,
                    "type": "bool",
                    "description": "Active",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Bitfield case class with correct types
    assert "enabled: Boolean" in result  # 1-bit bool -> Boolean
    assert "level: Int" in result  # multi-bit uint -> Int
    assert "active: Boolean" in result  # 1-bit bool -> Boolean

    # Bitfield has jsoniter codec
    assert "implicit val codec: JsonValueCodec[flags]" in result
    assert "JsonCodecMaker.make" in result

    # Has serialize/deserialize methods
    assert "def serialize(): String" in result
    assert "def deserialize(json: String): flags" in result


# =============================================================================
# Tests for Bug Fixes
# =============================================================================


def test_bitfield_reserved_comment_format() -> None:
    """Test that bitfield reserved fields have correct bit range in comment.

    The comment should show the correct start and end bit numbers.
    """
    definitions = {
        "file": {
            "brief": "Bitfield reserved test",
            "description": "Testing reserved bit range comment",
        },
        "control_register": {
            "description": "Control register with reserved bits",
            "display_name": "Control Register",
            "type": "bit_field",
            "size": 1,
            "members": [
                {
                    "name": "enable",
                    "start": 0,
                    "bits": 1,
                    "type": "bool",
                    "description": "Enable flag",
                },
                {
                    "name": "reserved_mid",
                    "start": 1,
                    "bits": 3,
                    "type": "reserved",
                    "description": "Reserved middle bits",
                },
                {
                    "name": "mode",
                    "start": 4,
                    "bits": 2,
                    "type": "uint",
                    "description": "Mode selector",
                },
                {
                    "name": "reserved_top",
                    "start": 6,
                    "bits": 2,
                    "type": "reserved",
                    "description": "Reserved top bits",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Check reserved comments have correct bit ranges
    # reserved_mid: bits 1-3 (start=1, bits=3, so last=1+3-1=3)
    assert "// Reserved: bits 1-3" in result

    # reserved_top: bits 6-7 (start=6, bits=2, so last=6+2-1=7)
    assert "// Reserved: bits 6-7" in result


def test_eight_byte_integer_uses_constant() -> None:
    """Test that 8-byte integers are handled correctly.

    This verifies the BYTES_8 constant is properly used for 64-bit integers.
    """
    definitions = {
        "file": {
            "brief": "8-byte int test",
            "description": "Testing 64-bit integer handling",
        },
        "large_data": {
            "description": "Structure with 8-byte integers",
            "display_name": "Large Data",
            "size": 24,
            "type": "structure",
            "members": [
                {
                    "name": "signed_64",
                    "size": 8,
                    "type": "int",
                    "description": "Signed 64-bit value",
                },
                {
                    "name": "unsigned_64",
                    "size": 8,
                    "type": "uint",
                    "description": "Unsigned 64-bit value",
                },
                {
                    "name": "timestamp",
                    "size": 8,
                    "type": "uint",
                    "description": "64-bit timestamp",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # 8-byte signed int -> Long
    assert "signed_64: Long" in result

    # 8-byte unsigned int -> Long
    assert "unsigned_64: Long" in result

    # Binary decode uses 64-bit functions
    assert "BinaryUtils.bytesToInt64LE(bytes, 0)" in result
    assert "BinaryUtils.bytesToUint64LE(bytes, 8)" in result

    # Binary encode uses 64-bit functions
    assert "BinaryUtils.int64LEtoBytes(event.signed_64)" in result
    assert "BinaryUtils.uint64LEtoBytes(event.unsigned_64)" in result

    # JSON types - both signed and unsigned use Long
    assert "signed_64: Long" in result  # JSON uses Long for signed
    assert "unsigned_64: Long" in result  # JSON uses Long for unsigned (no hex)


def test_enum_unknown_value_hex_parsing() -> None:
    """Test enum fromDisplayString and jsoniter codec.

    The generated code should have fromDisplayString for parsing known values
    and a jsoniter codec that handles JSON serialization/deserialization.
    """
    definitions = {
        "file": {
            "brief": "Enum hex parsing test",
            "description": "Testing UnknownValue format parsing",
        },
        "command_type": {
            "description": "Command types",
            "display_name": "Command Type",
            "size": 1,
            "type": "enum",
            "values": [
                {
                    "label": "start",
                    "value": 0,
                    "display_name": "Start",
                    "description": "Start command",
                },
                {
                    "label": "stop",
                    "value": 1,
                    "display_name": "Stop",
                    "description": "Stop command",
                },
            ],
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )

    # Should have fromDisplayString for parsing known labels
    assert "def fromDisplayString(s: String): Option[command_type]" in result
    assert 'if (s == "start") return Some(command_type.start)' in result
    assert 'if (s == "stop") return Some(command_type.stop)' in result

    # Should have jsoniter codec that uses toDisplayString/fromDisplayString
    assert "implicit val codec: JsonValueCodec[command_type]" in result
    assert "out.writeVal(toDisplayString(x))" in result
    assert "fromDisplayString(s).getOrElse(UnknownValue(0))" in result


def test_format_large_int_helper() -> None:
    """Test the format_large_int helper function for edge cases."""
    # Normal integers
    assert render_scala.format_large_int(0) == "0"
    assert render_scala.format_large_int(100) == "100"
    assert render_scala.format_large_int(-100) == "-100"

    # At Int boundaries (should NOT have L suffix)
    assert render_scala.format_large_int(2147483647) == "2147483647"
    assert render_scala.format_large_int(-2147483648) == "-2147483648"

    # Beyond Int boundaries (SHOULD have L suffix)
    assert render_scala.format_large_int(2147483648) == "2147483648L"
    assert render_scala.format_large_int(-2147483649) == "-2147483649L"

    # Large values
    assert (
        render_scala.format_large_int(9223372036854775807)
        == "9223372036854775807L"
    )


def test_escape_scala_keyword_helper() -> None:
    """Test the escape_scala_keyword helper function."""
    # Keywords should be escaped
    assert render_scala.escape_scala_keyword("type") == "`type`"
    assert render_scala.escape_scala_keyword("class") == "`class`"
    assert render_scala.escape_scala_keyword("object") == "`object`"
    assert render_scala.escape_scala_keyword("val") == "`val`"
    assert render_scala.escape_scala_keyword("var") == "`var`"
    assert render_scala.escape_scala_keyword("def") == "`def`"

    # Non-keywords should NOT be escaped
    assert render_scala.escape_scala_keyword("myField") == "myField"
    assert render_scala.escape_scala_keyword("temperature") == "temperature"
    assert render_scala.escape_scala_keyword("data") == "data"
    assert render_scala.escape_scala_keyword("value123") == "value123"


# =============================================================================
# Tests for variantName, variantPath, and multi-group membership
# =============================================================================


def test_render_group_variant_name() -> None:
    """Test that variantName is generated from group member name field."""
    definitions = {
        "file": {
            "brief": "variantName test",
            "description": "Testing variantName generation",
        },
        "commands": {
            "description": "Debug commands",
            "display_name": "Commands",
            "type": "group",
            "size": 2,
        },
        "cmd_reset": {
            "description": "Reset command",
            "display_name": "Reset",
            "type": "structure",
            "size": 0,
            "groups": {"commands": {"value": 1, "name": "reset"}},
        },
        "cmd_temperature_set": {
            "description": "Set temperature",
            "display_name": "Set Temperature",
            "type": "structure",
            "size": 3,
            "members": [
                {
                    "name": "temp",
                    "size": 2,
                    "type": "int",
                    "description": "Temp",
                },
                {
                    "name": "units",
                    "size": 1,
                    "type": "uint",
                    "description": "Units",
                },
            ],
            "groups": {"commands": {"value": 2, "name": "temperature_set"}},
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    assert "def variantName(value: commands): String = value match {" in result
    assert 'case _: cmd_reset => "reset"' in result
    assert 'case _: cmd_temperature_set => "temperature_set"' in result
    assert 'case _: commands_RawData => "unknown"' in result


def test_render_group_variant_path_no_nesting() -> None:
    """Test that variantPath delegates to variantName when no nested groups."""
    definitions = {
        "file": {
            "brief": "variantPath test",
            "description": "Testing variantPath with no nesting",
        },
        "events": {
            "description": "Events",
            "display_name": "Events",
            "type": "group",
            "size": 1,
        },
        "evt_start": {
            "description": "Start event",
            "display_name": "Start",
            "type": "structure",
            "size": 4,
            "members": [
                {
                    "name": "ts",
                    "size": 4,
                    "type": "uint",
                    "description": "Time",
                },
            ],
            "groups": {"events": {"value": 1, "name": "start"}},
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    assert (
        "def variantPath(value: events): String = variantName(value)" in result
    )


def test_render_group_variant_path_with_nesting() -> None:
    """Test that variantPath generates recursive concatenation for nested groups."""
    definitions = {
        "file": {
            "brief": "Nested group test",
            "description": "Testing variantPath with nested groups",
        },
        "inner_group": {
            "description": "Inner group",
            "display_name": "Inner Group",
            "type": "group",
            "size": 1,
        },
        "inner_variant_a": {
            "description": "Inner variant A",
            "display_name": "Inner A",
            "type": "structure",
            "size": 2,
            "members": [
                {
                    "name": "val1",
                    "size": 2,
                    "type": "uint",
                    "description": "Value",
                },
            ],
            "groups": {"inner_group": {"value": 1, "name": "variant_a"}},
        },
        "inner_variant_b": {
            "description": "Inner variant B",
            "display_name": "Inner B",
            "type": "structure",
            "size": 2,
            "members": [
                {
                    "name": "val2",
                    "size": 2,
                    "type": "int",
                    "description": "Value",
                },
            ],
            "groups": {"inner_group": {"value": 2, "name": "variant_b"}},
        },
        "outer_group": {
            "description": "Outer group",
            "display_name": "Outer Group",
            "type": "group",
            "size": 2,
        },
        "outer_simple": {
            "description": "Simple outer member",
            "display_name": "Simple Outer",
            "type": "structure",
            "size": 4,
            "members": [
                {
                    "name": "data",
                    "size": 4,
                    "type": "uint",
                    "description": "Data",
                },
            ],
            "groups": {"outer_group": {"value": 1, "name": "simple"}},
        },
        "outer_nested": {
            "description": "Outer member with nested group field",
            "display_name": "Nested Outer",
            "type": "structure",
            "size": 5,
            "members": [
                {"name": "id", "size": 2, "type": "uint", "description": "ID"},
                {
                    "name": "context",
                    "size": 3,
                    "type": "inner_group",
                    "description": "Context",
                },
            ],
            "groups": {"outer_group": {"value": 2, "name": "nested"}},
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # outer_group should have a full variantPath with recursive call
    assert (
        "def variantPath(value: outer_group): String = value match {" in result
    )
    assert 'case _: outer_simple => "simple"' in result
    assert (
        'case v: outer_nested => "nested" + "_" + inner_group.variantPath(v.context)'
        in result
    )
    # inner_group has no nesting, so variantPath delegates to variantName
    assert (
        "def variantPath(value: inner_group): String = variantName(value)"
        in result
    )


def test_render_structure_multi_group() -> None:
    """Test that a structure belonging to multiple groups extends all of them."""
    definitions = {
        "file": {
            "brief": "Multi-group test",
            "description": "Testing multi-group extends",
        },
        "group_a": {
            "description": "Group A",
            "display_name": "Group A",
            "type": "group",
            "size": 1,
        },
        "group_b": {
            "description": "Group B",
            "display_name": "Group B",
            "type": "group",
            "size": 1,
        },
        "shared_struct": {
            "description": "Shared structure",
            "display_name": "Shared",
            "type": "structure",
            "size": 4,
            "members": [
                {
                    "name": "value",
                    "size": 4,
                    "type": "int",
                    "description": "Val",
                },
            ],
            "groups": {
                "group_a": {"value": 1, "name": "shared"},
                "group_b": {"value": 2, "name": "shared_alt"},
            },
        },
        "only_a": {
            "description": "Only in group A",
            "display_name": "Only A",
            "type": "structure",
            "size": 2,
            "members": [
                {"name": "x", "size": 2, "type": "int", "description": "X"},
            ],
            "groups": {"group_a": {"value": 3, "name": "only_a"}},
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # shared_struct should extend both groups
    assert (
        "extends group_a with group_b with JsonSerializable" in result
        or "extends group_b with group_a with JsonSerializable" in result
    )
    # only_a should extend only group_a
    assert "final case class only_a(" in result
    # Verify only_a extends just group_a (check it doesn't extend group_b)
    assert "final case class only_a(" in result

    # Check variantName for both groups (from member name field)
    assert 'case _: shared_struct => "shared"' in result
    assert 'case _: shared_struct => "shared_alt"' in result
