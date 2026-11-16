"""Bounded JSON loading for stable, trusted local regular files."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat

from .core import AuditError, MAX_RECORDS, MAX_TOKEN

MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 64
MAX_NODES = 100_000
MAX_STRING = 16_384


@dataclass(frozen=True)
class _Number:
    token: str


def _number(token: str) -> _Number:
    if len(token) > MAX_TOKEN:
        raise AuditError(f"numeric tokens must be at most {MAX_TOKEN} characters")
    return _Number(token)


def _object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise AuditError("duplicate object member name")
        result[key] = value
    return result


def _constant(_: str) -> None:
    raise AuditError("nonstandard JSON numeric constant")


def _validate_tree(root: object) -> None:
    pending = [(root, 0)]
    nodes = 0
    while pending:
        value, depth = pending.pop()
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH:
            raise AuditError("JSON exceeds node or nesting limit")
        if isinstance(value, str):
            if len(value) > MAX_STRING or any(0xD800 <= ord(c) <= 0xDFFF for c in value):
                raise AuditError("JSON string exceeds limit or contains an unpaired surrogate")
        elif isinstance(value, dict):
            pending.extend((key, depth + 1) for key in value)
            pending.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            pending.extend((item, depth + 1) for item in value)


def load_numbers(path: str | Path, *, field: str | None = None) -> list[str]:
    """Read once, preserving number tokens. A field is a literal direct member.

    The bounded buffer and decoded document both reside in memory. This is not
    a streaming parser or protection against concurrent malicious path changes.
    """
    if field is not None and (type(field) is not str or len(field) > MAX_STRING or
                              any(0xD800 <= ord(c) <= 0xDFFF for c in field)):
        raise AuditError("field must be a bounded Unicode string")
    try:
        source = Path(path)
        metadata = source.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise AuditError("input must be a regular file, not a symlink or device")
        with source.open("rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise AuditError("input must be a regular file")
            data = stream.read(MAX_BYTES + 1)
    except (OSError, ValueError) as exc:
        if isinstance(exc, AuditError):
            raise
        raise AuditError("cannot read local input file") from None
    if len(data) > MAX_BYTES:
        raise AuditError(f"input exceeds {MAX_BYTES} bytes")
    try:
        root = json.loads(data.decode("utf-8"), parse_int=_number, parse_float=_number,
                          parse_constant=_constant, object_pairs_hook=_object)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise AuditError("invalid UTF-8 JSON or excessive nesting") from None
    _validate_tree(root)
    if type(root) is not list or len(root) > MAX_RECORDS:
        raise AuditError(f"root must be an array with at most {MAX_RECORDS} records")
    tokens = []
    for record, value in enumerate(root, 1):
        if field is not None:
            if type(value) is not dict or field not in value:
                raise AuditError(f"record {record}: missing selected direct numeric field")
            value = value[field]
        if not isinstance(value, _Number):
            raise AuditError(f"record {record}: selected value must be a JSON number")
        tokens.append(value.token)
    return tokens
