"""Version 1 benchmark contracts, independent of TADR check semantics."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]*$", max_length=160)]
Version = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$", max_length=80)]
Commit = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
PositiveInt = Annotated[int, Field(gt=0)]
NonnegativeInt = Annotated[int, Field(ge=0)]
Rate = Annotated[float, Field(ge=0, le=1)]
Score = Annotated[float, Field(ge=0, le=100)]
TaskType = Literal["classification", "regression", "time_series", "analytics"]
SourceFormat = Literal["csv", "parquet"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)


class TargetMetadata(Contract):
    target_name: Identifier = "tadr-core"
    target_package_version: Version
    target_source_distribution: Literal["proprietary"] = "proprietary"
    target_repository_url_or_null: None = None
    # Reviewed installation artifact bytes; never inferred from a source revision.
    target_installation_artifact_sha256: Digest | None = None
    target_algorithm_version: Version
    target_threshold_profile: Version
    target_bundle_protocol: Version
    target_baseline_revision: Version


class RepeatPolicy(Contract):
    warmup_runs: NonnegativeInt
    measurement_runs: PositiveInt


class InstrumentationPolicy(Contract):
    protocol_version: Literal["1.0"] = "1.0"
    timeout_seconds: Annotated[float, Field(gt=0)]
    memory_sampling_interval_seconds: Annotated[float, Field(gt=0)]
    process_scope: Literal["worker_and_children"] = "worker_and_children"
    runtime_scope: Literal["target_analyze"] = "target_analyze"
    rss_method: Literal["sampled_process_tree_rss"] = "sampled_process_tree_rss"


class DeterminismCase(Contract):
    case_id: Identifier
    python_hash_seed: NonnegativeInt
    timezone: Literal["UTC", "Europe/Berlin", "America/New_York"]
    decimal_precision: Annotated[int, Field(ge=1)]
    decimal_rounding: Literal["ROUND_HALF_EVEN", "ROUND_DOWN", "ROUND_UP"]
    fresh_process: Literal[True] = True


class PlannedScope(Contract):
    check_ids: list[Identifier]
    scenario_families: list[Identifier]
    studies: list[Identifier]
    notes: str


class AnalysisVariant(Contract):
    variant_id: Identifier
    constraints: dict[str, JsonValue]


class ScenarioSelector(Contract):
    include_prefixes: list[Identifier] = []
    include_ids: list[Identifier] = []
    exclude_ids: list[Identifier] = []

    @model_validator(mode="after")
    def finite_selection(self):
        if not (self.include_prefixes or self.include_ids):
            raise ValueError("selector must include scenarios")
        for values in (self.include_prefixes, self.include_ids, self.exclude_ids):
            if len(values) != len(set(values)):
                raise ValueError("duplicate selector entry")
        return self


class ExecutionGroup(Contract):
    group_id: Identifier
    selector: ScenarioSelector
    variant_ids: list[Identifier] = Field(min_length=1)
    context_ids: list[Identifier] = Field(min_length=1)
    repeat_policy: RepeatPolicy
    instrumentation_policy: InstrumentationPolicy

    @model_validator(mode="after")
    def unique_axes(self):
        if any(len(v) != len(set(v)) for v in (self.variant_ids, self.context_ids)):
            raise ValueError("duplicate execution-group axis")
        return self


class ExecutionReadiness(Contract):
    platform: Literal["Linux"] = "Linux"
    architecture: Literal["x86_64"] = "x86_64"
    python_version: Literal["3.11.9"] = "3.11.9"
    polars_max_threads: Literal[4] = 4
    host_provisioned: bool = False
    instrumentation_validated: bool = False
    target_artifact_verified: bool = False
    target_metadata_verified: bool = False


class CampaignManifest(TargetMetadata):
    campaign_id: Identifier
    status: Literal["planned", "ready", "frozen"]
    benchmark_protocol_version: Literal["1.0"] = "1.0"
    scenario_set_version: Version
    result_schema_version: Literal["1.0"] = "1.0"
    python_version: Version | None
    benchmark_package_version: Version
    benchmark_git_commit: Commit | None
    formats: list[SourceFormat] = Field(min_length=1)
    task_types: list[TaskType] = Field(min_length=1)
    scale_matrix: list[PositiveInt] = Field(min_length=1)
    repeat_policy: RepeatPolicy | None
    instrumentation_policy: InstrumentationPolicy | None
    scenario_ids: list[Identifier]
    determinism_cases: list[DeterminismCase]
    analysis_variants: list[AnalysisVariant]
    execution_groups: list[ExecutionGroup] = []
    execution_readiness: ExecutionReadiness | None = None
    planned_scope: PlannedScope
    frozen_date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")] | None = None

    @model_validator(mode="after")
    def campaign_state(self):
        for field in ("formats", "task_types", "scale_matrix", "scenario_ids"):
            values = getattr(self, field)
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {field}")
        if len({case.case_id for case in self.determinism_cases}) != len(self.determinism_cases):
            raise ValueError("duplicate determinism cases")
        if len({variant.variant_id for variant in self.analysis_variants}) != len(self.analysis_variants):
            raise ValueError("duplicate analysis variants")
        if len({g.group_id for g in self.execution_groups}) != len(self.execution_groups):
            raise ValueError("duplicate execution groups")
        if self.status != "planned":
            required = (self.target_installation_artifact_sha256, self.python_version,
                        self.execution_groups or (self.repeat_policy and self.instrumentation_policy),
                        self.scenario_ids, self.determinism_cases,
                        self.analysis_variants)
            if not all(required):
                raise ValueError("ready/frozen campaigns require an artifact fingerprint and exact provenance and execution policies")
            if self.campaign_id == "ALPHA_BENCHMARK_V1":
                ready = self.execution_readiness
                if not ready or not (ready.host_provisioned and ready.instrumentation_validated):
                    raise ValueError("Alpha requires a provisioned and validated execution host")
                if self.python_version != ready.python_version:
                    raise ValueError("Alpha Python protocol differs from execution environment")
                if not (ready.target_artifact_verified and ready.target_metadata_verified):
                    raise ValueError("Alpha requires verified target artifact and installed metadata")
        if self.status == "frozen" and self.benchmark_git_commit is None:
            raise ValueError("frozen manifest requires resolved benchmark revision")
        if self.campaign_id == "ALPHA_BENCHMARK_V1" and (
                self.target_name, self.target_package_version, self.target_algorithm_version,
                self.target_threshold_profile, self.target_bundle_protocol, self.target_baseline_revision
        ) != ("tadr-core", "0.1.0", "1.0", "MVP_V1", "1.0", "1.0.12"):
            raise ValueError("Alpha target metadata differs from the approved contract")
        if (self.status == "frozen") != (self.frozen_date is not None):
            raise ValueError("frozen_date is required only for frozen campaigns")
        if self.frozen_date:
            from datetime import date
            date.fromisoformat(self.frozen_date)
        return self


class FindingExpectation(Contract):
    id_pattern: str = Field(min_length=1)
    subject: str | None = None


class DefectSpec(Contract):
    defect_id: Identifier
    injector: Identifier
    injector_version: Version
    parameters: dict[str, JsonValue]
    affected_columns: list[str]


class GroundTruth(Contract):
    expected_findings: list[FindingExpectation]
    expected_absent_findings: list[FindingExpectation]
    expected_affected_columns: list[str]
    expected_gate_behavior: Literal["none", "present", "unconstrained"]
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def consistent(self):
        from .serialization import canonical_bytes
        present = [canonical_bytes(item) for item in self.expected_findings]
        absent = [canonical_bytes(item) for item in self.expected_absent_findings]
        if len(set(present)) != len(present) or len(set(absent)) != len(absent):
            raise ValueError("duplicate Finding expectations")
        if set(present) & set(absent):
            raise ValueError("same Finding cannot be both expected and absent")
        return self


class ScenarioSpec(GroundTruth):
    scenario_id: Identifier
    scenario_version: Version
    description: str = Field(min_length=1)
    task_type: TaskType
    task_parameters: dict[str, JsonValue]
    row_count: PositiveInt
    column_count: PositiveInt
    source_format: SourceFormat
    generator: Identifier
    generator_version: Version
    generator_parameters: dict[str, JsonValue]
    rng_algorithm: Identifier | None
    seed: NonnegativeInt | None
    defects: list[DefectSpec]
    tags: list[Identifier]

    @model_validator(mode="after")
    def explicit_randomness(self):
        if (self.rng_algorithm is None) != (self.seed is None):
            raise ValueError("RNG algorithm and seed must be declared together")
        if "task_type" in self.task_parameters:
            raise ValueError("task_type belongs in its explicit field")
        if len({item.defect_id for item in self.defects}) != len(self.defects):
            raise ValueError("duplicate defects")
        return self

    def ground_truth(self) -> GroundTruth:
        return GroundTruth(**{name: getattr(self, name) for name in GroundTruth.model_fields})


class DatasetArtifact(Contract):
    relative_path: str
    logical_dataset_sha256: Digest
    source_file_sha256: Digest
    scenario_sha256: Digest
    ground_truth: GroundTruth

    @field_validator("relative_path")
    @classmethod
    def working_dataset(cls, value):
        from .paths import safe_relative
        path = safe_relative(value)
        if path.parts[:2] != (".work", "datasets"):
            raise ValueError("generated datasets belong under .work/datasets")
        return value


class RunSpec(Contract):
    campaign_id: Identifier
    scenario_id: Identifier
    scenario_version: Version
    scenario_sha256: Digest
    run_id: Identifier
    repeat_index: NonnegativeInt
    phase: Literal["warmup", "measurement"]
    determinism_case_id: Identifier
    determinism_context: DeterminismCase
    analysis_variant: Identifier
    constraints: dict[str, JsonValue]
    execution_group_id: Identifier | None = None
    instrumentation_policy: InstrumentationPolicy

    @model_validator(mode="after")
    def context_identity(self):
        if self.determinism_case_id != self.determinism_context.case_id:
            raise ValueError("determinism context identity mismatch")
        return self


class EnvironmentInfo(Contract):
    os: str
    os_version: str | None
    architecture: str
    python_version: Version
    cpu_model: str | None
    physical_cpu_count: PositiveInt | None
    logical_cpu_count: PositiveInt | None
    total_memory_bytes: PositiveInt
    dependency_versions: dict[Identifier, Version]

    @model_validator(mode="after")
    def sanitized(self):
        from .safety import text_issues
        for field in ("os", "os_version", "architecture", "cpu_model"):
            value = getattr(self, field)
            if value and text_issues(value):
                raise ValueError(f"unsafe environment field: {field}")
        return self

    @property
    def environment_id(self) -> str:
        from .serialization import canonical_bytes, sha256
        return sha256(canonical_bytes(self))


class DetectionOutcome(Contract):
    matched_expectations: list[NonnegativeInt]
    missed_expectations: list[NonnegativeInt]
    violated_absent_expectations: list[NonnegativeInt]
    unexpected_finding_ids: list[str]
    gate_expectation_met: bool | None


class RunResult(TargetMetadata):
    result_schema_version: Literal["1.0"] = "1.0"
    benchmark_protocol_version: Literal["1.0"] = "1.0"
    campaign_id: Identifier
    scenario_id: Identifier
    scenario_version: Version
    scenario_sha256: Digest
    run_id: Identifier
    repeat_index: NonnegativeInt
    phase: Literal["warmup", "measurement"]
    determinism_case_id: Identifier
    determinism_context: DeterminismCase
    analysis_variant: Identifier
    constraints: dict[str, JsonValue]
    logical_dataset_sha256: Digest
    source_file_sha256: Digest
    benchmark_git_commit: Commit
    benchmark_package_version: Version
    task_type: TaskType
    source_format: SourceFormat
    row_count: PositiveInt
    column_count: PositiveInt
    analysis_mode: Identifier
    sample_ratio: Rate
    runtime_seconds: Annotated[float, Field(gt=0)]
    throughput_rows_per_second: Annotated[float, Field(ge=0)]
    peak_rss_bytes: NonnegativeInt
    cpu_utilization_percent: Annotated[float, Field(ge=0)] | None = None
    temporary_spill_bytes: NonnegativeInt | None = None
    temporary_spill_operations: NonnegativeInt | None = None
    source_scan_count: NonnegativeInt | None = None
    largest_logical_batch: PositiveInt | None = None
    readiness_score: Annotated[int, Field(ge=0, le=100)]
    report_confidence: Annotated[int, Field(ge=0, le=100)]
    total_risk: Score
    category_risks: dict[Identifier, Score]
    finding_ids: list[str]
    finding_severities: list[Identifier]
    finding_subjects: list[str]
    hard_gates: list[str]
    remediation_ids: list[str]
    expected_finding_ids_or_patterns: list[FindingExpectation]
    detection_outcome: DetectionOutcome
    canonical_report_sha256: Digest
    environment_id: Digest
    instrumentation_policy: InstrumentationPolicy
    execution_group_id: Identifier | None = None

    @model_validator(mode="after")
    def valid_record(self):
        import math
        if self.determinism_case_id != self.determinism_context.case_id:
            raise ValueError("determinism context identity mismatch")
        if self.target_installation_artifact_sha256 is None:
            raise ValueError("run records require an exact target artifact fingerprint")
        if not (len(self.finding_ids) == len(self.finding_subjects) == len(self.finding_severities)):
            raise ValueError("Finding fields must be positionally aligned")
        if len(set(self.finding_ids)) != len(self.finding_ids):
            raise ValueError("duplicate Finding IDs")
        if not math.isclose(self.throughput_rows_per_second,
                            self.row_count / self.runtime_seconds, rel_tol=1e-9):
            raise ValueError("throughput must be input rows divided by wall runtime")
        outcome = self.detection_outcome
        indexes = outcome.matched_expectations + outcome.missed_expectations
        if sorted(indexes) != list(range(len(self.expected_finding_ids_or_patterns))):
            raise ValueError("detection outcomes must partition positive expectations")
        return self


class SummaryGroup(Contract):
    scenario_id: Identifier
    scenario_version: Version
    analysis_variant: Identifier
    environment_id: Digest
    measured_runs: PositiveInt
    runtime_median_seconds: float
    runtime_min_seconds: float
    runtime_max_seconds: float
    runtime_mad_seconds: float
    throughput_median_rows_per_second: float
    peak_rss_median_bytes: float
    readiness_min: int
    readiness_max: int
    matched_expectations: NonnegativeInt
    missed_expectations: NonnegativeInt
    absent_violations: NonnegativeInt
    unexpected_findings: NonnegativeInt
    deterministic: bool
    determinism_case_id: Identifier = "standard"
    runtime_values_seconds: list[float] = []
    peak_rss_values_bytes: list[NonnegativeInt] = []
    weak_evidence: bool = False


class CampaignSummary(Contract):
    result_schema_version: Literal["1.0"] = "1.0"
    campaign_id: Identifier
    run_data_sha256: Digest
    groups: list[SummaryGroup]
    successful_runs: NonnegativeInt = 0
    adverse_target_outcomes: NonnegativeInt = 0
    failures_sha256: Digest | None = None
    attempts_sha256: Digest | None = None
    total_attempts: NonnegativeInt = 0
    infrastructure_retries: NonnegativeInt = 0
    resolved_infrastructure_failures: NonnegativeInt = 0


class ComparisonResult(Contract):
    comparison_schema_version: Literal["1.0"] = "1.0"
    left_run_id: Identifier
    right_run_id: Identifier
    detection_comparable: bool
    performance_comparable: bool
    reasons: list[str]
    finding_agreement: Rate | None
    severity_agreement: Rate | None
    readiness_score_delta: float | None
    report_confidence_delta: float | None
    hard_gates_changed: bool | None
    added_finding_ids: list[str]
    removed_finding_ids: list[str]
    runtime_delta_percent: float | None
    peak_rss_delta_percent: float | None
    throughput_delta_percent: float | None


class SamplingComparison(Contract):
    reference_run_id: Identifier
    sampled_run_id: Identifier
    finding_agreement: Rate
    severity_agreement: Rate | None
    readiness_score_delta: float
    report_confidence_delta: float
    total_risk_delta: float
    category_risk_deltas: dict[Identifier, float]
    missed_finding_ids: list[str] = []
    added_finding_ids: list[str] = []
    added_hard_gates: list[str] = []
    removed_hard_gates: list[str] = []
    primitive_deltas: dict[str, float | None] = {}
    primitive_unavailable_reasons: dict[str, str] = {}
