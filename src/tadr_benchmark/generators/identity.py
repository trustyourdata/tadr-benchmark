"""Container-independent logical identity and exact streaming file identity."""

import hashlib
from collections.abc import Iterable
from pathlib import Path

from ..companions import LogicalColumn
from ..serialization import canonical_bytes


def logical_dataset_sha256(schema: list[LogicalColumn], rows: Iterable[list], row_count: int) -> str:
    if row_count <= 0 or not schema or len({c.name for c in schema}) != len(schema):
        raise ValueError("logical identity requires positive dimensions and unique columns")
    digest = hashlib.sha256(canonical_bytes({"identity_version": "1.0", "row_count": row_count,
                                            "schema": [c.model_dump() for c in schema]}))
    count = 0
    types = {"string": str, "int64": int, "bool": bool}
    for row in rows:
        if len(row) != len(schema):
            raise ValueError("logical row width differs from schema")
        for column, value in zip(schema, row):
            if value is not None and type(value) is not types[column.logical_type]:
                raise ValueError("logical scalar type differs from schema")
            if column.logical_type == "int64" and value is not None and not -(2**63) <= value < 2**63:
                raise ValueError("logical int64 overflow")
        digest.update(canonical_bytes(row))
        count += 1
    if count != row_count:
        raise ValueError("logical row count differs from declared count")
    return digest.hexdigest()


def source_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
