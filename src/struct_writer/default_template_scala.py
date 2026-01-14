import tomllib
from typing import Any


def default_template() -> dict[str, Any]:
    template = """\
[file]
description = '''
/**
* @file
* @brief ${file.brief}
*
* ${file.description}
*
* @note This file is auto-generated using struct-writer
*        Pattern based on yule-common-parsing ByteSequence model
*/
'''

header = '''
package ${package}

import org.json4s._
import org.json4s.jackson.JsonMethods._
import org.json4s.jackson.Serialization

import scala.util.{Try, Success, Failure}
import scala.collection.mutable

// Binary utilities - implement these based on your project
object BinaryUtils {
  def bytesToUint8(bytes: Array[Byte], offset: Int): Int =
    bytes(offset) & 0xFF

  def bytesToUint16LE(bytes: Array[Byte], offset: Int): Int =
    ((bytes(offset) & 0xFF) | ((bytes(offset + 1) & 0xFF) << 8)) & 0xFFFF

  def bytesToUint32LE(bytes: Array[Byte], offset: Int): Long =
    ((bytes(offset) & 0xFF) |
     ((bytes(offset + 1) & 0xFF) << 8) |
     ((bytes(offset + 2) & 0xFF) << 16) |
     ((bytes(offset + 3) & 0xFF) << 24)) & 0xFFFFFFFFL

  def uint8ToBytes(value: Int): Byte = (value & 0xFF).toByte

  def uint16LEtoBytes(value: Int): Array[Byte] = Array(
    (value & 0xFF).toByte,
    ((value >> 8) & 0xFF).toByte
  )

  def uint32LEtoBytes(value: Long): Array[Byte] = Array(
    (value & 0xFF).toByte,
    ((value >> 8) & 0xFF).toByte,
    ((value >> 16) & 0xFF).toByte,
    ((value >> 24) & 0xFF).toByte
  )

  // Signed integer conversions
  def bytesToInt8(bytes: Array[Byte], offset: Int): Byte =
    bytes(offset)

  def bytesToInt16LE(bytes: Array[Byte], offset: Int): Short =
    ((bytes(offset) & 0xFF) | ((bytes(offset + 1) & 0xFF) << 8)).toShort

  def bytesToInt32LE(bytes: Array[Byte], offset: Int): Int =
    (bytes(offset) & 0xFF) |
    ((bytes(offset + 1) & 0xFF) << 8) |
    ((bytes(offset + 2) & 0xFF) << 16) |
    ((bytes(offset + 3) & 0xFF) << 24)

  def int8ToBytes(value: Byte): Byte = value

  def int16LEtoBytes(value: Short): Array[Byte] = Array(
    (value & 0xFF).toByte,
    ((value >> 8) & 0xFF).toByte
  )

  def int32LEtoBytes(value: Int): Array[Byte] = Array(
    (value & 0xFF).toByte,
    ((value >> 8) & 0xFF).toByte,
    ((value >> 16) & 0xFF).toByte,
    ((value >> 24) & 0xFF).toByte
  )

  def bytesToInt64LE(bytes: Array[Byte], offset: Int): Long =
    (bytes(offset) & 0xFFL) |
    ((bytes(offset + 1) & 0xFFL) << 8) |
    ((bytes(offset + 2) & 0xFFL) << 16) |
    ((bytes(offset + 3) & 0xFFL) << 24) |
    ((bytes(offset + 4) & 0xFFL) << 32) |
    ((bytes(offset + 5) & 0xFFL) << 40) |
    ((bytes(offset + 6) & 0xFFL) << 48) |
    ((bytes(offset + 7) & 0xFFL) << 56)

  def int64LEtoBytes(value: Long): Array[Byte] = Array(
    (value & 0xFF).toByte,
    ((value >> 8) & 0xFF).toByte,
    ((value >> 16) & 0xFF).toByte,
    ((value >> 24) & 0xFF).toByte,
    ((value >> 32) & 0xFF).toByte,
    ((value >> 40) & 0xFF).toByte,
    ((value >> 48) & 0xFF).toByte,
    ((value >> 56) & 0xFF).toByte
  )

  def bytesToUint64LE(bytes: Array[Byte], offset: Int): Long =
    (bytes(offset) & 0xFFL) |
    ((bytes(offset + 1) & 0xFFL) << 8) |
    ((bytes(offset + 2) & 0xFFL) << 16) |
    ((bytes(offset + 3) & 0xFFL) << 24) |
    ((bytes(offset + 4) & 0xFFL) << 32) |
    ((bytes(offset + 5) & 0xFFL) << 40) |
    ((bytes(offset + 6) & 0xFFL) << 48) |
    ((bytes(offset + 7) & 0xFFL) << 56)

  def uint64LEtoBytes(value: Long): Array[Byte] = Array(
    (value & 0xFF).toByte,
    ((value >> 8) & 0xFF).toByte,
    ((value >> 16) & 0xFF).toByte,
    ((value >> 24) & 0xFF).toByte,
    ((value >> 32) & 0xFF).toByte,
    ((value >> 40) & 0xFF).toByte,
    ((value >> 48) & 0xFF).toByte,
    ((value >> 56) & 0xFF).toByte
  )

  // Aliases for single-byte operations (no endianness for 1 byte)
  def bytesToInt8LE(bytes: Array[Byte], offset: Int): Byte = bytesToInt8(bytes, offset)
  def int8LEtoBytes(value: Byte): Array[Byte] = Array(value)
  def bytesToUint8LE(bytes: Array[Byte], offset: Int): Int = bytesToUint8(bytes, offset)
  def uint8LEtoBytes(value: Int): Array[Byte] = Array(uint8ToBytes(value))
}

// Base trait for all generated structures
trait ByteSequence {
  def SizeInBytes: Int
  def toByteSeq: Try[Seq[Byte]]
}

// Codec pattern
trait ByteSequenceCodec[T <: ByteSequence] {
  def SizeInBytes: Int
  def decode(bytes: Array[Byte], streamPositionHead: Long): Try[T]
  def encode(event: T): Try[Seq[Byte]]
  def decodeLogEvent(bytes: Array[Byte]): T
  def encodeLogEvent(event: T): Seq[Byte]
}

// JSON serialization trait (matches yule-parsing-common pattern)
trait CustomJsonSerializer {
  type ObjectToSerialize <: AnyRef

  implicit val formats: Formats = DefaultFormats

  def serialize(): String = Serialization.writePretty(getObjectToSerialize())
  def serializeToJValue(): JValue = parse(serialize())

  protected def getObjectToSerialize(): ObjectToSerialize
}

// JSON deserialization trait (matches yule-parsing-common pattern)
trait CustomJsonDeserializer[D <: AnyRef] {

  def deserialize(json: String): D = {
    implicit val formats: Formats = DefaultFormats
    fromJson(json)
  }

  def deserializeFromJValue(jValue: JValue): D = {
    val json = compact(render(jValue))
    deserialize(json)
  }

  protected def fromJson(json: String)(implicit formats: Formats): D
}

// Domain objects (placeholders - implement these based on your needs)
object Timestamp {
  def apply(epoch: Long, millis: Int): Timestamp = new Timestamp(epoch, millis)
  def deserialize(s: String): Timestamp = {
    // Parse ISO8601 or similar format - implement based on your needs
    new Timestamp(0, 0)  // Placeholder
  }
}
case class Timestamp(epoch: Long, millis: Int) {
  def serialize(): String = {
    // Format as ISO8601 or similar - implement based on your needs
    s"$epoch.$millis"  // Placeholder
  }
}

object Binary {
  def apply(value: Int, bits: Int): Binary = new Binary(value, bits)
  def deserialize(s: String): Binary = {
    // Parse binary string "0b..." - implement based on your needs
    new Binary(0, 0)  // Placeholder
  }
}
case class Binary(value: Int, bits: Int) {
  def serialize(): String = {
    val binaryStr = value.toBinaryString.reverse.padTo(bits, '0').reverse
    s"0b$binaryStr"
  }
}

object Hexadecimal {
  def apply(value: Int, bits: Int): Hexadecimal = new Hexadecimal(value, bits)
  def deserialize(s: String): Hexadecimal = {
    // Parse hex string "0x..." - implement based on your needs
    new Hexadecimal(0, 0)  // Placeholder
  }
}
case class Hexadecimal(value: Int, bits: Int) {
  def serialize(): String = {
    val hexDigits = (bits + 3) / 4  // Round up to nearest hex digit
    s"0x${value.toHexString.toUpperCase.reverse.padTo(hexDigits, '0').reverse}"
  }
}

'''

footer = '''

// End of generated code
'''

[group]
tag_name = '${group.name}_tag'

[structure]
type_name = '${structure.name}'

[enum]
type_name = '${enumeration.name}'

[bit_field]
type_name = '${bit_field.name}'

"""
    return tomllib.loads(template)
