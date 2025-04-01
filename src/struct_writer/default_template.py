import copy
import tomllib

from struct_writer import templating
from struct_writer.templating import named_tuple_from_dict


def new_default_template():
    render_functions = {
        "render_file_description": render_file_description,
        "render_file_header": render_file_header,
        "render_file_footer": render_file_footer,
        "render_structure_header": render_structure_header,
        "render_structure_footer": render_structure_footer,
    }
    return render_functions


def render_file_description(definitions):
    definitions = named_tuple_from_dict("definitions", definitions)
    return f"""\
/**
* @file
* @brief {definitions.file.brief}
*
* {definitions.file.description}
*
* @note This file is auto-generated using struct-writer
*/
"""


def render_file_header(definitions, **kwargs):
    definitions = copy.deepcopy(definitions)
    definitions = templating.merge(definitions, kwargs)
    definitions = named_tuple_from_dict("definitions", definitions)
    return f"""\
#ifndef {definitions.out_file.stem.upper()}_H_
#define {definitions.out_file.stem.upper()}_H_
#ifdef __cplusplus
extern "C" {{
#endif

#include <static_assert.h>
#include <stdint.h>

"""


def render_file_footer(definitions, **kwargs):
    definitions = copy.deepcopy(definitions)
    definitions = templating.merge(definitions, kwargs)
    definitions = named_tuple_from_dict("definitions", definitions)
    return f"""\
#ifdef __cplusplus
}}
#endif
#endif // {definitions.out_file.stem.upper()}_H_
"""


def render_structure_header(structure, _definitions, _templates):
    return f"""\
/// {structure.display_name}
/// {structure.description}
typedef struct {structure.name}_s{{
"""


def render_structure_footer(structure, _definitions, _templates):
    return f"""\
}} {structure.name}_t;
STATIC_ASSERT_TYPE_SIZE({structure.name}_t, {structure.size});

"""


def default_template():
    template = """\
[file]

[group]
tag_name = '${group.name}_tag'

[structure]
type_name = '${structure.name}_t'

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
void_pointer = '''
/// ${member.description}
void * ${member.name};
'''
bool = '''
/// ${member.description}
bool ${member.name}[${member.size}];
'''
bytes = '''
/// ${member.description}
uint8_t ${member.name}[${member.size}];
'''
str = '''
/// ${member.description}
char ${member.name}[${member.size}];
'''
union.footer = '''
} ${union.name};
'''
union.header = '''
union {
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
