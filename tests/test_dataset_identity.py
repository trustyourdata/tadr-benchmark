from hashlib import sha256

import pytest

from tadr_benchmark.companions import LogicalColumn
from tadr_benchmark.generators.identity import logical_dataset_sha256, source_file_sha256
from tadr_benchmark.generators.tabular import iter_rows
from tadr_benchmark.generators.writers import logical_schema, read_logical_source, read_source_schema, write_source
from tadr_benchmark.reporting.comparison import compare
from tadr_benchmark.scenarios.recipe import Recipe, recipe_from_id


def test_logical_hash_tracks_order_schema_nulls_and_scalar_types():
    schema = [LogicalColumn(name="x", logical_type="string")]
    rows = [["1"], [None]]
    expected_bytes = (b'{"identity_version":"1.0","row_count":2,"schema":[{"logical_type":"string","name":"x"}]}\n'
                      b'["1"]\n[null]\n')
    original = logical_dataset_sha256(schema, rows, 2)
    assert original == sha256(expected_bytes).hexdigest()
    assert logical_dataset_sha256(schema, list(reversed(rows)), 2) != original
    assert logical_dataset_sha256(schema, [["1"], [""]], 2) != original
    assert logical_dataset_sha256([LogicalColumn(name="x", logical_type="int64")], [[1], [None]], 2) != original
    with pytest.raises(ValueError, match="type"):
        logical_dataset_sha256([LogicalColumn(name="x", logical_type="int64")], [[True]], 1)
    with pytest.raises(ValueError, match="count"):
        logical_dataset_sha256(schema, rows, 3)


def test_source_hash_is_exact_bytes_including_newline_and_metadata(tmp_path):
    path = tmp_path / "fixture.csv"
    path.write_bytes(b"x\n1\n")
    original = source_file_sha256(path)
    assert original == sha256(b"x\n1\n").hexdigest()
    path.write_bytes(b"x\r\n1\r\n")
    assert source_file_sha256(path) != original


def test_csv_and_string_parquet_logical_equivalence_and_repeatable_bytes(tmp_path):
    # Small support fixture: no target calls, observations, or large source files.
    csv_recipe = recipe_from_id("leak.control.support49.csv")
    parquet_recipe = recipe_from_id("leak.control.support49.pqstr")
    csv_path, parquet_path = tmp_path / "tiny.csv", tmp_path / "tiny.parquet"
    write_source(csv_recipe, csv_path)
    write_source(parquet_recipe, parquet_path)
    assert logical_schema(csv_recipe) == logical_schema(parquet_recipe)
    assert read_source_schema(csv_path, "csv") == logical_schema(csv_recipe)
    assert read_source_schema(parquet_path, "pqstr") == logical_schema(parquet_recipe)
    expected_rows = list(iter_rows(csv_recipe))
    assert list(read_logical_source(csv_path, "csv")) == expected_rows
    assert list(read_logical_source(parquet_path, "pqstr")) == expected_rows
    hashes = [logical_dataset_sha256(logical_schema(r), read_logical_source(p, r.representation), 49)
              for r, p in [(csv_recipe, csv_path), (parquet_recipe, parquet_path)]]
    assert hashes[0] == hashes[1]
    assert source_file_sha256(csv_path) != source_file_sha256(parquet_path)
    assert b"\r" not in csv_path.read_bytes()
    assert not csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
    for r, original in [(csv_recipe, csv_path), (parquet_recipe, parquet_path)]:
        repeated = tmp_path / ("second."+r.representation)
        write_source(r, repeated)
        assert repeated.read_bytes() == original.read_bytes()
    import pyarrow.parquet as pq
    metadata = pq.ParquetFile(parquet_path).metadata
    assert metadata.num_row_groups == 1 and metadata.row_group(0).num_rows == 49
    assert metadata.row_group(0).column(0).compression == "ZSTD"
    assert "RLE_DICTIONARY" not in metadata.row_group(0).column(0).encodings


def test_null_transport_and_native_parquet_schema_on_tiny_intentional_fixtures(tmp_path):
    # Explicitly constructed unit fixture recipes, not registered campaign cases.
    for rep in ("csv", "pqstr"):
        r = Recipe(scenario_id="fixture.null."+rep, family="missing", case="feature", task="analytics",
                   row_count=10, count=3, representation=rep)
        path = tmp_path / ("null."+rep)
        write_source(r, path)
        assert sum(row[3] is None for row in read_logical_source(path, rep)) == 3
    native = Recipe(scenario_id="fixture.native", family="scale", case="analytics", task="analytics",
                    row_count=10, width=20, representation="pqnative")
    path = tmp_path / "native.parquet"
    write_source(native, path)
    decoded = list(read_logical_source(path, "pqnative"))
    assert len(decoded) == 10 and all(len(row) == 20 for row in decoded)
    assert type(decoded[0][0]) is int and type(decoded[0][5]) is bool
    assert read_source_schema(path, "pqnative") == logical_schema(native)
    assert decoded == list(iter_rows(native))


def test_regenerated_parquet_metadata_does_not_claim_identical_physical_input(tmp_path, completed):
    import pyarrow as pa
    import pyarrow.parquet as pq
    table = pa.table({"x": ["one", "two"]})
    first, second = tmp_path / "first.parquet", tmp_path / "second.parquet"
    pq.write_table(table, first)
    pq.write_table(table.replace_schema_metadata({b"fixture": b"changed"}), second)
    schema = [LogicalColumn(name="x", logical_type="string")]
    assert logical_dataset_sha256(schema, read_logical_source(first, "pqstr"), 2) == logical_dataset_sha256(
        schema, read_logical_source(second, "pqstr"), 2)
    assert source_file_sha256(first) != source_file_sha256(second)
    run = next(r for r in completed[0] if r.phase == "measurement")
    other = type(run).model_validate({**run.model_dump(), "source_file_sha256": "f"*64})
    result = compare(run, other, {run.environment_id: "approved_fixture_class"})
    assert result.detection_comparable and not result.performance_comparable
    assert result.runtime_delta_percent is None


def test_writer_refuses_unpinned_dependency_and_overwrite(tmp_path, monkeypatch):
    import pyarrow
    r = recipe_from_id("leak.control.support49.pqstr")
    monkeypatch.setattr(pyarrow, "__version__", "different")
    with pytest.raises(ValueError, match="pinned"):
        write_source(r, tmp_path / "new.parquet")
    path = tmp_path / "existing.csv"
    path.write_bytes(b"unchanged")
    with pytest.raises(ValueError, match="already exists"):
        write_source(recipe_from_id("leak.control.support49.csv"), path)
    assert path.read_bytes() == b"unchanged"
