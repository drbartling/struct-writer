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
    assert "import org.json4s._" in result
    assert "trait ByteSequence" in result
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


def test_render_file_with_structure() -> None:
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
    assert "extends ByteSequence with CustomJsonSerializer" in result
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
    assert "extends commands with CustomJsonSerializer" in result


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


def test_group_with_common_fields() -> None:
    """Test that common fields across group members become abstract methods."""
    definitions = {
        "file": {
            "brief": "Test file",
            "description": "Testing common fields",
        },
        "events": {
            "description": "Event group with common timestamp",
            "display_name": "Events",
            "type": "group",
            "size": 2,
        },
        "event_a": {
            "description": "First event type",
            "display_name": "Event A",
            "type": "structure",
            "size": 10,
            "members": [
                {
                    "name": "timestamp",
                    "size": 8,
                    "type": "uint",
                    "description": "Event timestamp",
                },
                {
                    "name": "value_a",
                    "size": 2,
                    "type": "uint",
                    "description": "Value specific to A",
                },
            ],
            "groups": {
                "events": {
                    "value": 1,
                    "name": "a",
                },
            },
        },
        "event_b": {
            "description": "Second event type",
            "display_name": "Event B",
            "type": "structure",
            "size": 12,
            "members": [
                {
                    "name": "timestamp",
                    "size": 8,
                    "type": "uint",
                    "description": "Event timestamp",
                },
                {
                    "name": "value_b",
                    "size": 4,
                    "type": "uint",
                    "description": "Value specific to B",
                },
            ],
            "groups": {
                "events": {
                    "value": 2,
                    "name": "b",
                },
            },
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # Common field should become abstract method on trait
    assert "sealed trait events extends ByteSequence {" in result
    assert "def timestamp: Long" in result
    # Member structures should still work
    assert "final case class event_a(" in result
    assert "final case class event_b(" in result


def test_raw_data_fallback_class() -> None:
    """Test that RawData fallback class is generated for groups."""
    definitions = {
        "file": {
            "brief": "Test file",
            "description": "Testing RawData fallback",
        },
        "commands": {
            "description": "Command group",
            "display_name": "Commands",
            "type": "group",
            "size": 2,
        },
        "cmd_reset": {
            "description": "Reset command",
            "display_name": "Reset",
            "type": "structure",
            "size": 0,
            "groups": {
                "commands": {
                    "value": 1,
                    "name": "reset",
                },
            },
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # RawData class should exist
    assert "final case class commands_RawData(" in result
    assert "tag: Int," in result
    assert "rawBytes: Array[Byte]" in result
    assert "extends commands with CustomJsonSerializer" in result
    # RawData JSON helper should exist
    assert "case class commands_RawDataJson(" in result
    # Fallback in match should use RawData instead of Failure
    assert "case _ => Success(commands_RawData(tag, structureBytes))" in result


def test_raw_data_with_common_fields() -> None:
    """Test that RawData provides default implementations for common fields."""
    definitions = {
        "file": {
            "brief": "Test file",
            "description": "Testing RawData with common fields",
        },
        "events": {
            "description": "Event group",
            "display_name": "Events",
            "type": "group",
            "size": 2,
        },
        "event_a": {
            "description": "Event A",
            "display_name": "Event A",
            "type": "structure",
            "size": 9,
            "members": [
                {
                    "name": "timestamp",
                    "size": 8,
                    "type": "uint",
                    "description": "Timestamp",
                },
                {
                    "name": "flag",
                    "size": 1,
                    "type": "bool",
                    "description": "Flag",
                },
            ],
            "groups": {
                "events": {
                    "value": 1,
                    "name": "a",
                },
            },
        },
        "event_b": {
            "description": "Event B",
            "display_name": "Event B",
            "type": "structure",
            "size": 10,
            "members": [
                {
                    "name": "timestamp",
                    "size": 8,
                    "type": "uint",
                    "description": "Timestamp",
                },
                {
                    "name": "flag",
                    "size": 1,
                    "type": "bool",
                    "description": "Flag",
                },
                {
                    "name": "extra",
                    "size": 1,
                    "type": "uint",
                    "description": "Extra field",
                },
            ],
            "groups": {
                "events": {
                    "value": 2,
                    "name": "b",
                },
            },
        },
    }
    template = default_template_scala.default_template()
    result = render_scala.render_file(
        definitions, template, Path("my_file.scala")
    )
    # RawData should have default implementations for common fields
    assert "events_RawData" in result
    # Check default values are provided
    assert "override def timestamp: Long = 0" in result
    assert "override def flag: Boolean = false" in result
