import csv
import io
import logging
from pathlib import Path
from typing import Any

from struct_writer.definitions import (
    BitField,
    DefinedType,
    Enumeration,
    Group,
    Structure,
    TypeDefinitions,
)
from struct_writer.templating import Template

_logger = logging.getLogger(__name__)

_DEFAULT_COLUMNS = [
    "category",
    "qualified_name",
    "display_name",
    "description",
    "data_type",
    "size_bytes",
    "details",
]


def render_file(
    definitions: dict[str, Any],
    templates: dict[str, Any],
    output_file: Path,
) -> str:
    """Render documentation rows into CSV text."""

    parsed_definitions = TypeDefinitions.from_dict(definitions)
    file_info = _file_to_dict(parsed_definitions.file_info)

    file_templates = templates.get("file", {})
    columns = list(file_templates.get("columns", _DEFAULT_COLUMNS))
    include_header = file_templates.get("include_header", True)

    common_context = {
        "file": file_info,
        "columns": columns,
        "out_file": output_file,
    }

    output = ""
    output += _render_optional_template(
        file_templates.get("description", ""),
        **common_context,
    )
    output += _render_optional_template(
        file_templates.get("header", ""),
        **common_context,
    )

    rows: list[list[str]] = []
    rows.append(
        _render_row(
            "file",
            templates,
            columns,
            output_file,
            {
                "file": file_info,
            },
        )
    )

    for name in sorted(parsed_definitions.definitions):
        rows.extend(
            _render_definition_rows(
                name,
                parsed_definitions.definitions,
                templates,
                columns,
                output_file,
            )
        )

    output += _rows_to_csv(columns, rows, include_header)
    output += _render_optional_template(
        file_templates.get("footer", ""),
        **common_context,
    )

    return output


def _render_definition_rows(
    name: str,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
    columns: list[str],
    output_file: Path,
) -> list[list[str]]:
    """
    Render a definition and its children to CSV rows.
    
    Args:
        name: The name of the definition to render
        definitions: All available type definitions
        templates: Template configuration for row rendering
        columns: List of column names for the CSV
        output_file: Path to the output file (for template context)
        
    Returns:
        List of CSV rows as lists of strings
    """
    definition = definitions[name]
    if isinstance(definition, Structure):
        return _render_structure_rows(definition, templates, columns, output_file)
    if isinstance(definition, Enumeration):
        return _render_enum_rows(definition, templates, columns, output_file)
    if isinstance(definition, Group):
        return _render_group_rows(
            definition,
            definitions,
            templates,
            columns,
            output_file,
        )
    if isinstance(definition, BitField):
        return _render_bit_field_rows(definition, templates, columns, output_file)
    _logger.debug("Skipping unsupported definition type for CSV: %s", name)
    return []


def _render_structure_rows(
    structure: Structure,
    templates: dict[str, Any],
    columns: list[str],
    output_file: Path,
) -> list[list[str]]:
    """
    Render a structure definition and its members to CSV rows.
    
    Args:
        structure: The structure to render
        templates: Template configuration for row rendering
        columns: List of column names for the CSV
        output_file: Path to the output file (for template context)
        
    Returns:
        List containing structure row followed by member rows
    """
    structure_dict = _structure_to_dict(structure)
    rows = [
        _render_row(
            "structure",
            templates,
            columns,
            output_file,
            {"structure": structure_dict},
        )
    ]
    for member in structure_dict.get("members", []):
        rows.append(
            _render_row(
                "structure_member",
                templates,
                columns,
                output_file,
                {
                    "structure": structure_dict,
                    "member": member,
                },
            )
        )
    return rows


def _render_enum_rows(
    enumeration: Enumeration,
    templates: dict[str, Any],
    columns: list[str],
    output_file: Path,
) -> list[list[str]]:
    """
    Render an enumeration and its values to CSV rows.
    
    Args:
        enumeration: The enumeration to render
        templates: Template configuration for row rendering
        columns: List of column names for the CSV
        output_file: Path to the output file (for template context)
        
    Returns:
        List containing enum row followed by value rows
    """
    enum_dict = _enum_to_dict(enumeration)
    rows = [
        _render_row(
            "enum",
            templates,
            columns,
            output_file,
            {"enumeration": enum_dict},
        )
    ]
    for value in enum_dict.get("values", []):
        rows.append(
            _render_row(
                "enum_value",
                templates,
                columns,
                output_file,
                {
                    "enumeration": enum_dict,
                    "value": value,
                },
            )
        )
    return rows


def _render_bit_field_rows(
    bit_field: BitField,
    templates: dict[str, Any],
    columns: list[str],
    output_file: Path,
) -> list[list[str]]:
    """
    Render a bit field and its members to CSV rows.
    
    Args:
        bit_field: The bit field to render
        templates: Template configuration for row rendering
        columns: List of column names for the CSV
        output_file: Path to the output file (for template context)
        
    Returns:
        List containing bit field row followed by member rows
    """
    bit_field_dict = _bit_field_to_dict(bit_field)
    rows = [
        _render_row(
            "bit_field",
            templates,
            columns,
            output_file,
            {"bit_field": bit_field_dict},
        )
    ]
    for member in bit_field_dict.get("members", []):
        rows.append(
            _render_row(
                "bit_field_member",
                templates,
                columns,
                output_file,
                {
                    "bit_field": bit_field_dict,
                    "member": member,
                },
            )
        )
    return rows


def _render_group_rows(
    group: Group,
    definitions: dict[str, DefinedType],
    templates: dict[str, Any],
    columns: list[str],
    output_file: Path,
) -> list[list[str]]:
    """
    Render a group and its tagged members to CSV rows.
    
    Args:
        group: The group to render
        definitions: All available type definitions for member lookup
        templates: Template configuration for row rendering
        columns: List of column names for the CSV
        output_file: Path to the output file (for template context)
        
    Returns:
        List containing group row followed by member rows
    """
    group_dict = _group_to_dict(group, definitions)
    rows = [
        _render_row(
            "group",
            templates,
            columns,
            output_file,
            {"group": group_dict},
        )
    ]
    for member in group_dict.get("members", []):
        member_type = member.get("type_definition", {})
        rows.append(
            _render_row(
                "group_member",
                templates,
                columns,
                output_file,
                {
                    "group": group_dict,
                    "member": member,
                    "member_type": member_type,
                },
            )
        )
    return rows


def _render_row(
    row_type: str,
    templates: dict[str, Any],
    columns: list[str],
    output_file: Path,
    context: dict[str, Any],
) -> list[str]:
    rows_section = templates.get("rows", {})
    row_template = rows_section.get(row_type) or rows_section.get("default")
    if row_template is None:
        msg = f"Missing template configuration for row type '{row_type}'"
        raise KeyError(msg)

    eval_context = {
        **context,
        "row_type": row_type,
        "out_file": output_file,
        "columns": columns,
    }

    rendered_row: list[str] = []
    for column in columns:
        template_string = str(row_template.get(column, ""))
        if template_string:
            rendered_row.append(
                Template(template_string).safe_render(**eval_context)
            )
        else:
            rendered_row.append("")
    return rendered_row


def _rows_to_csv(
    columns: list[str],
    rows: list[list[str]],
    include_header: bool,
) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    if include_header:
        writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


def _render_optional_template(template_string: str, **context: Any) -> str:
    if not template_string:
        return ""
    return Template(str(template_string)).safe_render(**context)


def _file_to_dict(file_info: Any) -> dict[str, Any]:
    return {
        "brief": file_info.brief,
        "description": file_info.description,
    }


def _structure_to_dict(structure: Structure) -> dict[str, Any]:
    structure_dict = structure.to_dict()
    structure_dict["member_count"] = len(structure.members)
    return structure_dict


def _enum_to_dict(enumeration: Enumeration) -> dict[str, Any]:
    enum_dict = enumeration.to_dict()
    values = []
    for value in enum_dict.get("values", []):
        new_value = dict(value)
        new_value["hex_value"] = f"0x{value['value']:X}"
        values.append(new_value)
    enum_dict["values"] = values
    enum_dict["value_count"] = len(values)
    if values:
        enum_dict["min_value"] = min(v["value"] for v in values)
        enum_dict["max_value"] = max(v["value"] for v in values)
    else:
        enum_dict["min_value"] = None
        enum_dict["max_value"] = None
    enum_dict["value_labels"] = ", ".join(v["label"] for v in values)
    enum_dict["is_signed"] = any(v["value"] < 0 for v in values)
    signed_prefix = "i" if enum_dict["is_signed"] else "u"
    enum_dict["repr_type"] = f"{signed_prefix}{enum_dict['size'] * 8}"
    return enum_dict


def _bit_field_to_dict(bit_field: BitField) -> dict[str, Any]:
    bit_field_dict = bit_field.to_dict()
    bit_field_dict["bit_width"] = bit_field_dict["size"] * 8
    members = []
    for member in bit_field_dict.get("members", []):
        new_member = dict(member)
        start = int(new_member.get("start", 0))
        bits = int(new_member.get("bits", 0))
        if bits > 0:
            end = start + bits - 1
            new_member["bit_range"] = f"{start}..{end}"
        else:
            new_member["bit_range"] = ""
        members.append(new_member)
    bit_field_dict["members"] = members
    return bit_field_dict


def _group_to_dict(
    group: Group,
    definitions: dict[str, DefinedType],
) -> dict[str, Any]:
    group_dict = group.to_dict()
    group_dict["member_count"] = len(group.members)
    group_dict["tag_bits"] = group.size * 8
    members = []
    payload_sizes: list[int] = []
    for member in group.members:
        member_info = {
            "name": member.name,
            "type": member.type,
            "value": member.value,
        }
        definition = definitions.get(member.type)
        type_summary = _definition_summary(definition)
        member_info["type_definition"] = type_summary
        payload_size = int(type_summary.get("size", 0) or 0)
        member_info["payload_size"] = payload_size
        members.append(member_info)
        payload_sizes.append(payload_size)
    group_dict["members"] = members
    group_dict["max_payload_size"] = max(payload_sizes or [0])
    return group_dict


def _definition_summary(definition: DefinedType | None) -> dict[str, Any]:
    if definition is None:
        return {
            "name": "",
            "display_name": "",
            "description": "",
            "size": 0,
            "type": "",
        }
    summary = definition.to_dict()
    return {
        "name": summary.get("name", ""),
        "display_name": summary.get("display_name", summary.get("name", "")),
        "description": summary.get("description", ""),
        "size": summary.get("size", 0),
        "type": summary.get("type", ""),
    }
