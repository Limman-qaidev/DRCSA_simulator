"""Lightweight YAML loader tailored for the repository fixtures."""

from __future__ import annotations

from typing import Any


def safe_load(stream: Any) -> Any:
    if hasattr(stream, "read"):
        text = stream.read()
    else:
        text = str(stream)
    lines = [
        line.rstrip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    data, index = _parse_block(lines, 0, 0)
    if index != len(lines):
        raise ValueError("Unexpected trailing lines in YAML input")
    return data


def _parse_block(
    lines: list[str],
    start: int,
    indent: int,
) -> tuple[dict[str, Any], int]:
    index = start
    result: dict[str, Any] = {}
    while index < len(lines):
        line = lines[index]
        current_indent = len(line) - len(line.lstrip(" "))
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError("Invalid indentation in YAML input")
        key, _, remainder = line.strip().partition(":")
        if not _:
            raise ValueError("Missing ':' in YAML line")
        value = remainder.strip()
        if not value:
            next_index = index + 1
            if next_index < len(lines) and lines[
                next_index
            ].lstrip().startswith("- "):
                items: list[Any] = []
                index = next_index
                while index < len(lines):
                    line = lines[index]
                    current_indent = len(line) - len(line.lstrip(" "))
                    if current_indent < indent + 2:
                        break
                    if current_indent > indent + 2:
                        message = "Invalid indentation in YAML sequence"
                        raise ValueError(message)
                    stripped_item = line.strip()[2:].strip()
                    if stripped_item:
                        items.append(_parse_scalar(stripped_item))
                        index += 1
                    else:
                        nested, index = _parse_block(
                            lines, index + 1, indent + 4
                        )
                        items.append(nested)
                result[key] = items
                continue
            nested, index = _parse_block(lines, index + 1, indent + 2)
            result[key] = nested
        else:
            result[key] = _parse_scalar(value)
            index += 1
    return result, index


def _parse_scalar(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


__all__ = ["safe_load"]
