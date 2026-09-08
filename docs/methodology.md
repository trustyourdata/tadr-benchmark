# Evaluation methodology

## Objective and experimental units

Evaluate the reproducibility, detection behavior, score response and resource
cost of task-aware dataset readiness assessment. The unit of scientific design
is a versioned scenario with explicit task, dimensions, generation rules and
independent conditions. Repeats measure execution variability; repeating an
identical scenario does not create independent evidence about a population.

## Controlled synthetic data

Prefer deterministic construction with exact defect locations and magnitudes.
Where randomness is useful, specify the RNG algorithm, seed, generator version
and dependency implementation. Record checksums of generated content. Hold
unrelated factors constant when changing one defect. Specify how CSV and Parquet
encode equivalent semantics, including nulls, numeric strings and timestamps.
If equivalence is impossible, define separate scenarios and explain the difference.

Clean controls should cover applicable tasks, formats and relevant schema shapes.
Single-defect families isolate behavior; composite families study interactions
such as duplicates with unsafe group splits, parse failures with missingness,
direct leakage with ordinary quality issues, or invalid timestamps with unsafe
splits. Observe suppression and hard gates without reproducing target logic.

## Ground truth and boundaries

Author expectations before observing the target. Declare injected conditions,
Finding families/subjects, explicit absent Findings, affected columns and gate
expectations. Pattern matching uses case-sensitive shell-style glob patterns on
Finding IDs; an optional subject restricts the match to an exact subject key.
Each expectation is satisfied by at least one match. Unexpected Finding IDs are
retained separately. Avoid overlapping positive patterns when estimating rates.

Threshold studies require below/exact/above cases, including integer rounding of
defect counts. Derive threshold values from the reviewed target specification for
the pinned revision; record them as scenario parameters, not benchmark scoring
code. Sampling may alter the observed population, so distinguish an injection's
known full-data rate from a target's sampled estimate.

## Detection and negative controls

Raw outcomes retain matched and missed positive expectations, violated explicit
absences, unexpected Findings and gate agreement. A miss does not crash the
harness. Unexpected Findings merit examination; they are not automatically false
positives unless ground truth explicitly excludes that condition.

Future precision, recall and false-positive-rate analyses must predeclare their
units and denominators: scenario, subject, defect instance or check opportunity.
Report support counts and applicability exclusions. Undefined denominators stay
undefined, not zero. This foundation reports expectation counts; it does not
silently assign statistical meanings to them. Preserve failures and negative
controls alongside favorable cases.

## Scores, hard gates and suppression

Characterize readiness, confidence, total/category risks and hard-gate response
over controlled magnitudes. Evaluate monotonicity and boundary behavior as
experimental questions. Do not encode numeric scores as detection ground truth.
A future explicit score-regression experiment needs a separately reviewed contract.
Retain ordered Findings, severities, subjects and remediation IDs. The final
report may omit suppressed Findings; do not reconstruct them using copied Core
semantics. Composite cases can reveal observable effects without revealing all
internal causes.

## Determinism

Compare original target canonical bytes and SHA-256 hashes across repetitions,
fresh processes, Python hash seeds, timezones and caller Decimal contexts.
Ordered Findings, scores, category risks and confidence are retained for diagnosis.
A canonical mismatch is a determinism failure, not timing noise. It remains a
reportable negative result; publication validation does not erase it. Do not
sort target Finding arrays to make disagreement disappear.

## Sampling fidelity

Pair a full-data reference with `HEAD_STRIDE_V1` for the same target, scenario,
dataset and semantic context. Record sample ratio, analysis mode, Finding Jaccard
agreement, severity agreement on common Findings, confidence delta, readiness
delta and total/category-risk deltas. Empty Finding sets agree at 1; severity
agreement without common Findings is undefined.

Later placement studies should include head, middle, tail and positions between
selected strides. Avoid extrapolating from a few conveniently placed defects to
all distributions. Full-data references may use chunked execution so long as
the complete population is analyzed.

## Performance, scale and robustness

Choose a useful subset of the 10k/100k/1M/5M pilot candidates. Separate warmups
from measured runs and preserve every requested record. Configure timeout,
memory sampling interval, process scope and repetition policy explicitly.
Measure wall time around target analysis, throughput as input rows/wall seconds,
and sampled peak worker-tree RSS. Report optional CPU, spill, source-scan and
batch metrics only when actually instrumented. Throughput based on input rows
must not be described as analyzed-row throughput for sampled execution.

Use medians, dispersion and raw repeats; avoid conclusions from one timing.
MAD denotes median absolute deviation, without an implied confidence interval.
Control background load, storage/cache conditions, dependency versions and power
settings. An approved environment class is a reviewed claim of measurement
equivalence, not an automatic comparison of CPU or OS strings.

Robustness studies may later vary column widths, skew, cardinality, malformed
input and task/schema mismatch. Define expected infrastructure errors separately
from valid reports that miss defects. No error is silently converted to a
successful zero-risk record.

## Real-world data, ablations and statistical principles

Add external data only with explicit public provenance and redistribution terms.
See the dataset registry policy. Synthetic construction offers controlled truth
but lacks many interactions in real data; observational datasets often lack
complete defect labels. Report those uncertainties rather than treating target
outputs as labels.

Future ablations may isolate sampling, check availability or policy changes,
with distinct campaign IDs. Predeclare comparisons and denominators before
examining results. Separate the immutable common scenario subset from expanded
coverage. Any confidence intervals or significance procedures require a justified
sampling model; no such procedure is implied by the initial aggregate counts.

## Limitations

Alpha covers Check Set A and fixed heuristic `MVP_V1` thresholds, not Check Sets
B/C. Model-free readiness diagnostics do not establish fairness, downstream model
quality or production safety. Bounded sampling may miss structured defects;
sampled RSS may miss short peaks. Controlled synthetic performance is not a
universal hardware claim. The pilot alone is insufficient grounds to recalibrate
the target. Software test success validates the harness, not these research claims.
