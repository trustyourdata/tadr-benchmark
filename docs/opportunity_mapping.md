# Alpha opportunity mapping

The mapping is derived from versioned recipes and independent expectations before
reading target reports. It appears in the generated scenario matrix, including
scenario, subject, track, physical defect identity, positivity and mapped detectors.
The evaluator rejects duplicate physical identities. It never constructs negative
subjects from observed Findings.

Normative opportunities use each declared expected or absent check/subject.
Numeric/datetime recipe columns define parse opportunities; the declared timestamp
defines timestamp opportunities. Independently labeled identifier/measurement
columns define cardinality opportunities. Missingness uses candidate features and
the present supervised target. Duplication uses the dataset and declared key subject.
Classification uses its target; time/group checks use declared temporal/entity
subjects. Inference uses candidate features with null-list guards separated.
Leakage uses the named candidate feature/target pairs. Support, collapsed-target,
applicability and policy controls remain separate strata.

The controlled-condition track maps physical counts and roles to warning families.
Nonzero missingness, parser corruption, excess copies and repeated participants
remain positive below normative warning thresholds. Physical labels do not change
when sampling misses the condition. Class rarity is departure from the balanced
constructed target; collapsed support is separate. Legitimate measurement and
lexical identifier challenges are separate from primary clean controls. Allowlisted
target copies remain policy controls rather than universally safe negatives.

## Shared entity condition

`entity.cross_split_exposure` contributes exactly one physical opportunity per
scenario, physical defect ID and entity subject. It is detected when either final
`split.group_split_recommended` or `split.group_leakage_risk` Finding has that same
subject. Both together still contribute only one TP; neither contributes one FN
for a positive condition. The mapped detector IDs that fired remain diagnostic
detail. Sampling placement of repeated entities uses the same physical identity.

Normative conformance remains check-specific. For repeated share from 0.05 through
less than 0.20 and a non-group split, the recommendation is expected. At share at
least 0.20, random split expects the stronger risk Finding and suppresses the
same-entity recommendation; time split expects the recommendation. Group split
expects neither. A wrong warning can therefore detect the physical condition
while failing normative conformance.

Suppression has its own preregistered denominator: the stronger same-entity risk
Finding must be present and the weaker recommendation absent. Both Findings mean
one physical TP but failed normative conformance and failed suppression. Independent
row/key duplicate Findings are not part of this suppression pair.

## Denominators and descriptive queries

Finding evaluation requires a successful canonical TADRReport. A positive
opportunity is TP when detected and FN when missed in that successful report.
Negative opportunities similarly require a successful report for FP or TN.
A selected terminal outcome without a report is **UNEVALUABLE** and contributes
none of TP/FP/FN/TN. Failure is not a negative prediction. Gate, suppression and
normative conformance observations also remain unevaluable without a report.

Physical opportunities remain unique by scenario, defect ID and subject.
Normative opportunities remain expected/absent check-specific Findings; suppression
uses its separately preregistered opportunities. These supports are never mixed.
The three reporting layers have distinct denominators:

| Metric | Numerator | Denominator |
| --- | --- | --- |
| `conditional_recall` | TP | TP + FN, from successful reports |
| `conditional_precision` | TP | TP + FP, from successful reports |
| `conditional_fpr` | FP | FP + TN, from successful reports |
| `successful_report_coverage` | Planned opportunities with successful reports | All planned opportunities |
| `end_to_end_detection_yield` | Detected positive physical opportunities | All planned positive physical opportunities, including those without reports |

Every ratio retains its raw numerator and denominator. Undefined ratios remain
null. End-to-end detection yield describes the complete pipeline; it is not
recall, sensitivity or a true-positive rate. It is not a normative Finding metric.
Out-of-frame Findings remain visible separately from conditional fixed-frame FPR.

For example, 50 planned positive opportunities with 47 evaluable opportunities,
45 detections, two successful-report misses and three opportunities without reports
give conditional recall 45/47, successful-report coverage 47/50 and end-to-end
detection yield 45/50. This is an illustrative arithmetic example, not Alpha data.

Coverage is weighted by opportunities, not reports: a scenario with several
opportunities contributes all of them. Tables retain planned, evaluable and
unevaluable opportunity counts, separately for positive and negative classes,
alongside successful reports and terminal failures by category. The classes respect
the declared severity cutoff; physical presence does not change with that cutoff.
Report counts must not be substituted for opportunity denominators.

Typed target rejection, target analysis failure, timeout and resource termination
remain distinct selected terminal categories. Resolved infrastructure attempts
are operational history only; the selected outcome determines report availability.
An unfinished working query also discloses pending reports. Unresolved infrastructure
or missing selected outcomes still blocks freeze.

Scientific detection queries use only standard-context measured repeat zero, by
format and stratum, at INFO-inclusive and LOW-or-higher cutoffs. Formats remain
correlated representations, not independent datasets. Scenario detection and
all-required detection are separate from per-check metrics. Severity, localization,
gate/cap and suppression correctness retain their own evaluable support. Every
conditional precision/recall/FPR table row carries planned/evaluable denominators,
report coverage and terminal-failure counts, grouped by check, format, analysis
variant and scenario stratum. High conditional agreement with incomplete coverage
must remain visible. The detection figure pairs conditional recall with positive
report coverage and, for the physical track, end-to-end detection yield.

Clean-control and separate specificity-challenge tables retain failed planned
cells, their unevaluable negative opportunities and undefined Finding counts/FPR.
They never treat a missing report as a clean report. Missing reports do not produce
invented scores or performance measurements. Scale/sampling/retry counts do not
inflate primary correctness support.
