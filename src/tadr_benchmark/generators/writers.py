"""Explicit initial-version CSV and Parquet serialization; no target calls."""

import csv
from itertools import islice
from pathlib import Path

from ..companions import DatasetIdentity, LogicalColumn, WriterPolicy
from ..models import DatasetArtifact, ScenarioSpec
from ..paths import contained
from ..scenarios.expectations import expectations_for
from ..scenarios.recipe import Recipe, column_names
from ..serialization import canonical_bytes, sha256
from .identity import logical_dataset_sha256, source_file_sha256
from .tabular import iter_rows


def logical_schema(r: Recipe) -> list[LogicalColumn]:
    columns = []
    for name in column_names(r):
        kind = "string"
        if r.representation == "pqnative":
            kind = "bool" if name == "flag" else "string" if name in {"segment", "event_time"} else "int64"
        columns.append(LogicalColumn(name=name, logical_type=kind))
    return columns


def write_source(r: Recipe, destination: Path) -> None:
    """Low-level writer for intentional fixtures or an explicitly requested dataset.

    Callers own the destination. Exclusive creation prevents accidental overwrite.
    Native Parquet is limited to the approved scale representation.
    """
    if r.representation == "pqnative" and r.family != "scale":
        raise ValueError("native Parquet is an approved scale representation only")
    if destination.exists():
        raise ValueError("source destination already exists")
    if r.representation == "csv":
        with destination.open("x", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter=",", quotechar='"', doublequote=True,
                                quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
            writer.writerow(column_names(r))
            for row in iter_rows(r):
                if any(value == "" for value in row if value is not None):
                    raise ValueError("literal empty strings conflict with the declared CSV null encoding")
                writer.writerow(["" if value is None else value for value in row])
        return
    import pyarrow as pa
    import pyarrow.parquet as pq
    policy = WriterPolicy(representation=r.representation)
    if pa.__version__ != policy.pyarrow_version:
        raise ValueError("Parquet writer dependency differs from pinned version")
    kinds = {"string": pa.string(), "int64": pa.int64(), "bool": pa.bool_()}
    schema = pa.schema([pa.field(c.name, kinds[c.logical_type], nullable=True) for c in logical_schema(r)])
    rows = iter(iter_rows(r))
    with destination.open("xb") as stream:
        with pq.ParquetWriter(stream, schema, version=policy.parquet_version,
                              compression=policy.compression, compression_level=policy.compression_level,
                              use_dictionary=policy.use_dictionary, write_statistics=policy.write_statistics,
                              data_page_version=policy.data_page_version, data_page_size=policy.data_page_size,
                              write_batch_size=policy.write_batch_size, store_schema=True,
                              write_page_index=False, write_page_checksum=False,
                              use_byte_stream_split=False) as writer:
            while batch := list(islice(rows, policy.row_group_size)):
                arrays = [pa.array(values, type=field.type) for field, values in zip(schema, zip(*batch))]
                writer.write_table(pa.Table.from_arrays(arrays, schema=schema), row_group_size=policy.row_group_size)


def read_logical_source(path: Path, representation: str):
    """Independent container decoding for software validation and regeneration."""
    if representation == "csv":
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            next(reader)
            for row in reader:
                yield [None if value == "" else value for value in row]
    elif representation in {"pqstr", "pqnative"}:
        import pyarrow.parquet as pq
        for batch in pq.ParquetFile(path).iter_batches(batch_size=4096):
            yield from (list(row.values()) for row in batch.to_pylist())
    else:
        raise ValueError("unknown source representation")


def read_source_schema(path: Path, representation: str) -> list[LogicalColumn]:
    if representation == "csv":
        with path.open(encoding="utf-8", newline="") as stream:
            return [LogicalColumn(name=name, logical_type="string") for name in next(csv.reader(stream))]
    if representation not in {"pqstr", "pqnative"}:
        raise ValueError("unknown source representation")
    import pyarrow as pa
    import pyarrow.parquet as pq
    mapping = {pa.string(): "string", pa.int64(): "int64", pa.bool_(): "bool"}
    fields = pq.read_schema(path)
    if any(field.type not in mapping for field in fields):
        raise ValueError("physical schema has an unsupported logical type")
    return [LogicalColumn(name=field.name, logical_type=mapping[field.type]) for field in fields]


def dataset_identity(scenario: ScenarioSpec, artifact: DatasetArtifact) -> DatasetIdentity:
    r = Recipe.model_validate(scenario.generator_parameters)
    if artifact.scenario_sha256 != sha256(canonical_bytes(scenario)):
        raise ValueError("dataset artifact differs from scenario")
    return DatasetIdentity(scenario_id=scenario.scenario_id, scenario_version=scenario.scenario_version,
        scenario_sha256=artifact.scenario_sha256, logical_dataset_sha256=artifact.logical_dataset_sha256,
        source_file_sha256=artifact.source_file_sha256, logical_schema=logical_schema(r), row_count=r.row_count,
        writer_policy=WriterPolicy(representation=r.representation))


class AlphaDatasetGenerator:
    def generate(self, scenario: ScenarioSpec, repository: Path) -> DatasetArtifact:
        expectations_for(scenario)  # Reject altered snapshots; never consult a target.
        r = Recipe.model_validate(scenario.generator_parameters)
        suffix = "csv" if r.representation == "csv" else "parquet"
        relative = f".work/datasets/{scenario.scenario_id}.{suffix}"
        destination = contained(repository, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_source(r, destination)
        if read_source_schema(destination, r.representation) != logical_schema(r):
            raise ValueError("written source schema differs from recipe")
        logical_hash = logical_dataset_sha256(logical_schema(r), iter_rows(r), r.row_count)
        decoded_hash = logical_dataset_sha256(logical_schema(r), read_logical_source(destination, r.representation), r.row_count)
        if logical_hash != decoded_hash:
            raise ValueError("written source differs from the independently generated logical dataset")
        return DatasetArtifact(relative_path=relative, logical_dataset_sha256=logical_hash,
            source_file_sha256=source_file_sha256(destination), scenario_sha256=sha256(canonical_bytes(scenario)),
            ground_truth=scenario.ground_truth())
