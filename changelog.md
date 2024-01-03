# struct-writer Change Log

## 0.4.4

### Features
- Support python 3.11 - 3.12

## 0.4.3

### Change
- Remove the _u from the group union structure name

## 0.4.2

### Fixes
- Generate bit-mask correctly when parsing bit-fields


## 0.4.1

### Fixes
- Handle bytes and str data types when parsing bytes

## 0.4.0

### Features
- Convert from bytes to json using provided definitions
- Assert structures' size matches the total of the member sizes

### Change
- Group definitions now require `size` attribute

## 0.3.1

### Features
-  Convert bit-fields into bytestrings

## 0.3.0

### Features
- Add bit-field type to definitions
- Generate bit-field code from templates and definitions
