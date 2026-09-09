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
the pinned implementation; record them as scenario parameters, not benchmark scoring
code. Sampling may alter the observed population, so distinguish an injection's
known full-data rate from a target's sampled estimate.

## Detection and negative controls

The [Alpha opportunity mapping](opportunity_mapping.md) specifies the fixed subject
frames, separate physical and normative denominators, shared entity OR detection,
and independent suppression evaluation. It also defines the three reporting layers:
Finding rates conditional on successful canonical reports, opportunity-weighted
successful-report coverage, and separate end-to-end physical detection yield.
Selected failures without reports are UNEVALUABLE for Finding evaluation; they
are not false negatives or negative predictions. Conditional rates must always be
read alongside coverage and the separate failure taxonomy.

Raw outcomes retain matched and missed positive expectations, violated explicit
absences, unexpected Findings and gate agreement. A miss does not crash the
harness. Unexpected Findings merit examination; they are not automatically false
positives unless ground truth explicitly excludes that condition.

Precision, recall and false-positive-rate analyses must predeclare their
units and denominators: scenario, subject, defect instance or check opportunity.
Report support counts and applicability exclusions. Undefined denominators stay
undefined, not zero. Reporting retains fixed-frame counts and descriptive ratios;
these do not imply population accuracy. Preserve failures and negative
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

The approved Alpha definitions include head, middle, tail and unselected-stride
placements at 300k rows. Full-reference and bounded arms use logical planning
budgets of 4096 and 256 MiB, respectively. Reference mode must actually be full;
the bounded population must be 200k rows. The unchanged public target cannot
provide full execution above 500k, so 1M/5M cases have no claimed full reference.
Missingness, parse and timestamp counters use full scans even in sampled mode;
duplicate, cardinality, class, entity and leakage statistics can depend on P.

## Performance, scale and robustness

The Alpha manifest fixes fourteen selected 10k/100k/1M/5M scale cases. Separate warmups
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

## Alpha design and completed evidence

Versioned families deterministically expand to 370 concrete specifications, with
320 correctness cases, 36 sampling placements and 14 scale points. The source
manifest retains the historical READY launch declaration. The
[frozen report](../results/campaigns/alpha_benchmark_v1/REPORT.md) presents the
completed evidence and annotation history. The [Alpha benchmark protocol](alpha_benchmark_protocol.md) records
the fixed execution and source representation policies.

Original physical/design labels remain unchanged historical evidence. The approved
post-execution normative overlay corrects omitted category-cap annotations and
the event_key contract frame from the pre-existing Algorithm 1.0 contract. Original
and adjudicated results must both be published with their own denominators. A
valid identifier's contract-required parse warning remains adverse practical
specificity. Physical truth and the eight primary-clean registrations are unchanged.

Labels have three separate layers: physical conditions, pinned-Alpha normative
expectations, and research challenges. The eight clean task/representation
registrations define the primary clean-control denominator. Legitimate
high-cardinality measurements and the lexical-name challenge are assessed
separately for specificity; an expected INFO Finding is retained as contract
conformance and never hidden or counted in the primary clean-control FP rate.
Parser dominance loss, collapsed class support and nonreciprocal target encodings
can be contract-conformant no-Findings while remaining sensitivity limitations.

Planned precision/recall/FPR use predeclared check/subject opportunities and print
numerators and denominators. Out-of-frame Findings, applicability guards, and
undefined denominators are reported separately. Use standard-context repeat zero
for detection; contexts/repeats and paired formats are correlated observations.
No population confidence intervals, calibration or universal accuracy claims
follow from this engineered corpus.

Freeze distinguishes sound adverse target outcomes from broken infrastructure.
Input rejection, target analysis failure and censored timeout/resource termination
require independently validated inputs, typed safe codes and adjudication. They
count toward terminal coverage and completed-report failure rates. Infrastructure
failure, unknown context or missing monitor evidence blocks a freeze. Misses,
false positives and canonical disagreement in otherwise valid reports remain
research outcomes, with original observations preserved.

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
