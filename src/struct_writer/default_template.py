import tomllib


def default_template():
    template = """\
[file]
description = '''
/**
* @file
* @brief ${file.brief}
*
* ${file.description}
*
* @note This file is auto-generated using structured_api
*/
'''
header = '''
#ifndef ${out_file.stem.upper()}_H_
#define ${out_file.stem.upper()}_H_
#ifdef __cplusplus
extern "C" {
#endif

#include <static_assert.h>
#include <stdint.h>

'''
footer = '''
#ifdef __cplusplus
}
#endif
#endif // ${out_file.stem.upper()}_H_
'''

[group]
tag_name = '${group.name}_tag'

[union]
type_name = '${union.name}_t'
header = '''
/// ${union.display_name}
/// ${union.description}
typedef union ${union.name}_u{
'''
footer = '''
} ${union.name}_t;
STATIC_ASSERT_TYPE_SIZE(${union.name}_t, ${union.size});

'''

[structure]
type_name = '${structure.name}_t'
header = '''
/// ${structure.display_name}
/// ${structure.description}
typedef struct ${structure.name}_s{
'''
footer = '''
} ${structure.name}_t;
STATIC_ASSERT_TYPE_SIZE(${structure.name}_t, ${structure.size});

'''

[structure.members]
default = '''
/// ${member.description}
${member.type}_t ${member.name};
'''
empty = '''
/// Structure is intentionally empty (zero sized)
uint8_t empty[0];
'''
int = '''
/// ${member.description}
int${member.size*8}_t ${member.name};
'''
uint = '''
/// ${member.description}
uint${member.size*8}_t ${member.name};
'''

[enum]
header = '''
/// ${enumeration.display_name}
/// ${enumeration.description}
typedef enum ${enumeration.name}_e{
'''
footer = '''
} ${enumeration.name}_t;
STATIC_ASSERT_TYPE_SIZE(${enumeration.name}_t, ${enumeration.size});

'''
default = '''
/// ${value.description}
${enumeration.name}_${value.label},
'''
valued = '''
/// ${value.description}
${enumeration.name}_${value.label} = ${value.value:#x},
'''

[bit_field]
type_name = '${bit_field.name}_t'
header = '''
/// ${bit_field.display_name}
/// ${bit_field.description}
typedef struct ${bit_field.name}_s{
'''
footer = '''
} ${bit_field.name}_t;
STATIC_ASSERT_TYPE_SIZE(${bit_field.name}_t, ${bit_field.size});

'''

[bit_field.members]
default = '''
/// ${member.description}
${member.type}_t ${member.name}:${member.bits};
'''
reserved = '''
uint${bit_field.size*8}_t reserved_${member.start}:${member.bits};
'''
int = '''
/// ${member.description}
int${bit_field.size*8}_t ${member.name}:${member.bits};
'''
uint = '''
/// ${member.description}
uint${bit_field.size*8}_t ${member.name}:${member.bits};
'''
"""
    template = tomllib.loads(template)
    return template
