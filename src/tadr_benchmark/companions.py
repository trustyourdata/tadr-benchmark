"""Initial-version independent labels and allowlisted observation companions.

These contracts contain no target imports, reports, scoring or oracle calls.
"""

from math import gcd
from typing import Annotated, Literal

from pydantic import Field, JsonValue, model_validator

from .models import (Commit, Contract, DeterminismCase, Digest, Identifier, NonnegativeInt, PositiveInt,
                     Rate, RunSpec, Score, TargetMetadata, Version)


class RowRange(Contract):
    start: NonnegativeInt
    stop: PositiveInt
    step: PositiveInt = 1

    @model_validator(mode="after")
    def nonempty(self):
        if self.start >= self.stop:
            raise ValueError("row ranges are nonempty and half open")
        return self

    @property
    def count(self) -> int:
        return len(range(self.start, self.stop, self.step))


class RowMask(Contract):
    """Compact exact positions, including disjoint stride residues; no RNG."""
    row_count: PositiveInt
    ranges: list[RowRange] = []

    @model_validator(mode="after")
    def bounded_disjoint(self):
        for i, a in enumerate(self.ranges):
            if a.stop > self.row_count:
                raise ValueError("row mask exceeds dataset")
            for b in self.ranges[:i]:
                lower, upper = max(a.start, b.start), min(a.stop, b.stop)
                divisor = gcd(a.step, b.step)
                if lower >= upper or (b.start-a.start) % divisor:
                    continue
                modulus = b.step // divisor
                k = 0 if modulus == 1 else ((b.start-a.start)//divisor *
                                            pow(a.step//divisor, -1, modulus)) % modulus
                first = a.start + a.step*k
                period = a.step*b.step//divisor
                first += max(0, (lower-first+period-1)//period)*period
                if first < upper:
                    raise ValueError("overlapping row masks")
        return self

    @property
    def count(self) -> int:
        return sum(item.count for item in self.ranges)

    def contains(self, index: int) -> bool:
        return any(r.start <= index < r.stop and (index-r.start) % r.step == 0 for r in self.ranges)

    def rank(self, index: int) -> int:
        """Zero-based rank in ascending selected positions; caller checks membership."""
        return sum(len(range(r.start, min(index, r.stop), r.step))
                   for r in self.ranges if index > r.start)


class CountRatio(Contract):
    numerator: NonnegativeInt
    denominator: NonnegativeInt

    @model_validator(mode="after")
    def valid_counts(self):
        if self.numerator > self.denominator:
            raise ValueError("numerator exceeds denominator")
        return self


class PhysicalCondition(Contract):
    condition_id: Identifier
    columns: list[str]
    masks: dict[Identifier, RowMask] = {}
    counts: dict[Identifier, CountRatio] = {}
    description: str = Field(min_length=1)


class PhysicalLedger(Contract):
    annotation_version: Literal["1.0"] = "1.0"
    scenario_id: Identifier
    row_count: PositiveInt
    column_names: list[str] = Field(min_length=1)
    conditions: list[PhysicalCondition]

    @model_validator(mode="after")
    def consistent(self):
        if len(set(self.column_names)) != len(self.column_names):
            raise ValueError("duplicate logical columns")
        if len({c.condition_id for c in self.conditions}) != len(self.conditions):
            raise ValueError("duplicate physical condition")
        for condition in self.conditions:
            if any(m.row_count != self.row_count for m in condition.masks.values()):
                raise ValueError("physical mask row count differs")
        return self


class NormativeFinding(Contract):
    check_id: Identifier
    subject: str = Field(min_length=1)
    severity: Literal["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    population: Literal["metadata", "full", "P"]
    confidence: Rate | None = None


class GateExpectation(Contract):
    kind: Literal["direct_leakage", "missing_at_inference", "invalid_timestamp"]
    cap: Literal[50, 60, 70]

    @model_validator(mode="after")
    def correct_cap(self):
        if self.cap != {"direct_leakage": 60, "missing_at_inference": 70, "invalid_timestamp": 50}[self.kind]:
            raise ValueError("gate kind/cap mismatch")
        return self


class SuppressionExpectation(Contract):
    winner: Identifier
    loser: Identifier
    subject: str


class ResearchChallenge(Contract):
    challenge_id: Identifier
    interpretation: Literal["specificity", "sensitivity", "eligibility", "policy_control"]
    condition_present: bool
    description: str = Field(min_length=1)
    primary_clean_control_eligible: Literal[False] = False


class VariantExpectations(Contract):
    variant_id: Identifier
    findings: list[NormativeFinding]
    absent_check_ids: list[Identifier]
    gates: list[GateExpectation]
    suppressions: list[SuppressionExpectation] = []
    expected_category_caps: dict[Identifier, Score] = {}

    @model_validator(mode="after")
    def consistent(self):
        identities = [(f.check_id, f.subject) for f in self.findings]
        if len(set(identities)) != len(identities):
            raise ValueError("duplicate normative Finding")
        if {f.check_id for f in self.findings} & set(self.absent_check_ids):
            raise ValueError("present check declared absent")
        if len({g.kind for g in self.gates}) != len(self.gates):
            raise ValueError("duplicate gate")
        for s in self.suppressions:
            if (s.winner, s.subject) not in identities or (s.loser, s.subject) in identities:
                raise ValueError("invalid suppression expectation")
        return self


class ScenarioExpectations(Contract):
    annotation_version: Literal["1.0"] = "1.0"
    scenario_id: Identifier
    scenario_version: Version
    scenario_sha256: Digest
    physical: PhysicalLedger
    normative: list[VariantExpectations] = Field(min_length=1)
    challenges: list[ResearchChallenge] = []
    primary_clean_control_eligible: bool

    @model_validator(mode="after")
    def identity(self):
        if self.physical.scenario_id != self.scenario_id:
            raise ValueError("ledger scenario mismatch")
        if len({v.variant_id for v in self.normative}) != len(self.normative):
            raise ValueError("duplicate expectation variant")
        if self.challenges and self.primary_clean_control_eligible:
            raise ValueError("research challenges cannot enter primary clean controls")
        return self


class LogicalColumn(Contract):
    name: str = Field(min_length=1)
    logical_type: Literal["string", "int64", "bool"]


class WriterPolicy(Contract):
    writer_version: Literal["1.0"] = "1.0"
    representation: Literal["csv", "pqstr", "pqnative"]
    pyarrow_version: Literal["25.0.1"] = "25.0.1"
    encoding: Literal["utf-8"] = "utf-8"
    row_group_size: Literal[100000] = 100000
    parquet_version: Literal["2.6"] = "2.6"
    compression: Literal["zstd"] = "zstd"
    compression_level: Literal[3] = 3
    use_dictionary: Literal[False] = False
    write_statistics: Literal[True] = True
    data_page_version: Literal["1.0"] = "1.0"
    data_page_size: Literal[1048576] = 1048576
    write_batch_size: Literal[1024] = 1024


class DatasetIdentity(Contract):
    identity_version: Literal["1.0"] = "1.0"
    scenario_id: Identifier
    scenario_version: Version
    scenario_sha256: Digest
    logical_dataset_sha256: Digest
    source_file_sha256: Digest
    logical_schema: list[LogicalColumn] = Field(min_length=1)
    row_count: PositiveInt
    writer_policy: WriterPolicy

    @model_validator(mode="after")
    def unique_schema(self):
        if len({c.name for c in self.logical_schema}) != len(self.logical_schema):
            raise ValueError("duplicate dataset schema columns")
        if self.writer_policy.representation in {"csv", "pqstr"} and any(
                c.logical_type != "string" for c in self.logical_schema):
            raise ValueError("string transports require a string logical schema")
        return self


class RunFailure(TargetMetadata, RunSpec):
    result_schema_version: Literal["1.0"] = "1.0"
    benchmark_protocol_version: Literal["1.0"] = "1.0"
    benchmark_git_commit: Commit
    benchmark_package_version: Version
    logical_dataset_sha256: Digest
    source_file_sha256: Digest
    environment_id: Digest
    failure_kind: Literal["infrastructure", "target_input_rejection", "target_analysis_failure",
                          "timeout", "resource_abort"]
    stage: Literal["preflight", "startup", "analyze", "report_validation", "monitor", "serialization"]
    error_code: Literal["input_rejected", "dataset_read", "analysis_resource", "internal_analysis",
                        "unexpected_target_exception", "deadline_exceeded", "rss_limit",
                        "dataset_integrity", "provenance", "context", "instrumentation", "transport"]
    exception_class: Literal["InputValidationError", "DatasetReadError", "UnsupportedFormatError",
                             "AnalysisResourceError", "InternalAnalysisError", "ValidationError",
                             "UnexpectedTargetException"] | None = None
    independently_validated_input: bool
    adjudication: Literal["pending", "valid_target_outcome", "infrastructure_failure"]
    elapsed_seconds: Annotated[float, Field(ge=0)] | None = None
    policy_limit: Annotated[float, Field(gt=0)] | None = None

    @model_validator(mode="after")
    def honest_terminal_state(self):
        if self.target_git_commit is None:
            raise ValueError("failure requires exact target provenance")
        if self.adjudication == "valid_target_outcome" and (
                self.failure_kind == "infrastructure" or not self.independently_validated_input
                or self.stage != "analyze"):
            raise ValueError("infrastructure failures cannot become target outcomes")
        allowed = {
            "target_input_rejection": {"input_rejected", "dataset_read"},
            "target_analysis_failure": {"analysis_resource", "internal_analysis", "unexpected_target_exception"},
            "timeout": {"deadline_exceeded"}, "resource_abort": {"rss_limit"},
            "infrastructure": {"dataset_integrity", "provenance", "context", "instrumentation", "transport"}}
        if self.error_code not in allowed[self.failure_kind]:
            raise ValueError("failure code/kind mismatch")
        if self.failure_kind in {"timeout", "resource_abort"} and self.policy_limit is None:
            raise ValueError("censored outcomes require the enforced policy limit")
        return self


class OutcomeAccounting(Contract):
    planned: NonnegativeInt
    successful: NonnegativeInt
    adverse_target_outcomes: NonnegativeInt
    infrastructure_failures: NonnegativeInt
    unresolved: NonnegativeInt


class InstrumentationRecord(Contract):
    protocol_version: Literal["1.0"] = "1.0"
    run_id: Identifier
    baseline_rss_bytes: NonnegativeInt | None
    sample_count: NonnegativeInt
    maximum_sample_gap_seconds: Annotated[float, Field(ge=0)] | None
    analysis_start_acknowledged: bool
    analysis_end_acknowledged: bool
    effective_context_confirmed: bool
    polars_max_threads: PositiveInt
    terminal_state: Literal["success", "failure"]
    rss_abort_limit_bytes: PositiveInt | None
    unavailable_reason: Literal["not_supported", "monitor_failed", "no_samples"] | None = None


class DiagnosticValue(Contract):
    value: Annotated[float, Field(ge=0)] | None
    unavailable_reason: Literal["not_exposed", "not_applicable", "diagnostic_failed"] | None

    @model_validator(mode="after")
    def absence_is_not_zero(self):
        if (self.value is None) != (self.unavailable_reason is not None):
            raise ValueError("unavailable diagnostic requires a reason, never invented zero")
        return self


class DiagnosticRecord(TargetMetadata):
    diagnostic_version: Literal["1.0"] = "1.0"
    primary_run_id: Identifier
    scenario_id: Identifier
    scenario_sha256: Digest
    benchmark_git_commit: Commit
    logical_dataset_sha256: Digest
    source_file_sha256: Digest
    environment_id: Digest
    analysis_variant: Identifier
    determinism_case_id: Identifier
    determinism_context: DeterminismCase
    constraints: dict[str, JsonValue]
    auxiliary: Literal[True] = True
    analysis_mode: Literal["full", "chunked", "sampled"]
    sample_ratio: Rate
    metrics: dict[Literal["row_excess", "key_excess", "distinct_count", "nonmissing_count",
                          "class_count", "minority_count", "repeated_entity_participants",
                          "complete_pairs", "equality_matches", "mapping_matches",
                          "parse_attempts", "parse_failures", "missing_count"], DiagnosticValue]
