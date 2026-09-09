# ALPHA_BENCHMARK_V1 annotation adjudication review

**READY FOR FREEZE REVIEW**

Original whole-cell conformance is **234/320 (73.1250%)**. The approved contract-label corrections produce **320/320 (100.0000%)** on the same 320 correctness reports. This value was recomputed from corrected labels and unchanged report fields; it was not used as a target for the calculation.

Remaining: **CRITICAL 0; IMPORTANT 2; MINOR 1**. Counts concern benchmark validity and publication interpretation, not favorable target performance. Valid-identifier parse warnings remain an adverse Alpha result. This is eligibility for freeze review; no freeze or public release occurred.

## Evidence and processing scope

| Binding | Value |
| --- | --- |
| Scientific execution revision, unchanged | `a76bb9458b181500c7bfb9efefcfecfbb019b5a9` |
| Benchmark processing revision, unchanged | `4887bd579d394de523bab0ccb227840d66447fd9` |
| Target | tadr-core 0.1.0; proprietary; Algorithm 1.0; MVP_V1; AnalysisBundle 1.0; implementation baseline 1.0.12 |
| Approved wheel SHA-256 | `a37ec8d336d16dbe4b7a7448071808daaf5e3e0ab03afe3bb7de0ce6882bc31d` |
| Retained evidence | 578 selected outcomes and canonical reports; 13 warmups and 565 measured primary outcomes; 72 diagnostics; 370 source identities; original attempts and instrumentation |
| Scientific environment | Ubuntu 24.04 under WSL2; Linux x86_64; Python 3.11.9; POLARS_MAX_THREADS=4; WSL-native ext4 scientific storage |
| Adjudication | Deterministic benchmark-side annotation/evaluation processing; zero target imports and zero scientific invocations |

The original candidate, annotations, scenario hashes and scientific review remain byte-for-byte intact. The correction is a supplemental processing overlay. Editing original scenario snapshots would change scientific identities; deriving new physical opportunities from the new normative subject would change the physical denominator. Neither occurred. Original runs.jsonl detection fields and original tables retain their historical evaluation and must not be presented as adjudicated values.

The [machine-readable adjudication](adjudication.json) contains every full old and corrected annotation, old and corrected normative frame, scenario identity/hash, category, justification, contract-rule references and per-cell metric effect. The [corrected annotation overlay](corrected_normative_annotations.json), [adjudicated scenario metrics](adjudicated_scenario_metrics.json), [adjudicated scenario table](tables/adjudicated_scenario_matrix.csv) and [adjudicated detection table](tables/adjudicated_detection_by_check.csv) accompany it. The original whole-cell result is retained permanently as annotation history.

The [processing provenance](adjudication_provenance.json) identifies supplemental operator scripts by content hash and records the actual Windows annotation-processing environment separately from Linux scientific execution. It does not claim uncommitted operator scripts belong to the existing processing commit. The [bundle checksums](checksums.sha256) bind the supplemental artifacts. No benchmark, result, instrumentation, scenario or annotation version changed.

## Pre-execution contract basis

The rules were derived from the pre-existing Algorithm 1.0 contract in the approved wheel, not selected from observed outcomes. Static inspection and hashes bind 14 relevant module texts to that wheel; no proprietary source text or private source revision is copied here. [Contract rules, symbols and member hashes](contract_basis.json) provide the exact basis.

### C1: Algorithm 1.0 category cap / implementation baseline 1.0.12

For each final Finding, category weight times severity base times canonical Finding confidence; sum per category; cap at 40 and emit category_cap only when the uncapped sum is strictly greater than 40. CRITICAL base=28; leakage weight=1.6; inference_mismatch weight=1.3.

Members and symbols: `tadr/config/scoring.py`: `CATEGORY_CAP`, `CATEGORY_WEIGHTS`, `SEVERITY_BASE`; `tadr/contracts/enums.py`: `Category`, `Severity`; `tadr/core/scoring.py`: `finding_penalty`, `score_findings`.

### C2: Pre-existing evidence confidence for the affected full-reference recipes

Full-scan equality leakage uses EXACT_FULL_SCAN base .97, full coverage, no parse penalty and no stability flag; support multiplier is 1 at n>=1000, .95 at n>=200, .85 at n>=50, else .70. Confidence rounds HALF_UP to two decimals before scoring: .97 at n=10000; .92 at n=200. Metadata inference presence uses .99 without a row penalty. Reciprocal-mapping leakage uses STATISTICAL .88 at full coverage and n>=1000, remaining below the category-cap threshold for one Finding.

Members and symbols: `tadr/config/confidence.py`: `BASE_CONFIDENCE`, `ROW_STABILITY`, `PRESENCE_CHECKS`; `tadr/core/confidence.py`: `finding_confidence`, `confidence_for_finding`; `tadr/core/numeric_policy.py`: `quantize`, `canonical_confidence`; `tadr/checks/leakage.py`: `evaluate`; `tadr/checks/inference.py`: `evaluate`.

### C3: Pre-existing event name heuristic and expected datetime coercion

DATE_NAMES includes event. A string column whose lower-case name contains a date-name token is a datetime candidate and receives expected_type=datetime independently of its reported inferred_type. This expected-type rule does not exempt identifier roles. For the existing non-null event_<integer> values, datetime coercion has zero successes and the full population supplies attempts and failures.

Members and symbols: `tadr/analyzer/parsing.py`: `DATE_NAMES`, `parse_datetime`; `tadr/analyzer/type_inference.py`: `datetime_candidate`, `expected_type`; `tadr/analyzer/profiler.py`: `_profile`.

### C4: Pre-existing schema.parse_failures applicability and severity

The expected datetime column is eligible for schema.parse_failures. A nonzero attempt population with failure fraction 1 is above the existing HIGH threshold .20 (LOW .01; MEDIUM .05), so column:event_key has a HIGH final Finding with full-scan counter population. No new confidence assertion is added to the annotation. The contract explains observed confidence .62 through STATISTICAL .88 and minimum parse factor .70, rounded HALF_UP.

Members and symbols: `tadr/checks/applicability.py`: `candidates`; `tadr/checks/schema.py`: `evaluate`; `tadr/config/thresholds.py`: `CHECK_THRESHOLDS`; `tadr/config/confidence.py`: `BASE_CONFIDENCE`, `MIN_PARSE_FACTOR`; `tadr/core/confidence.py`: `finding_confidence`.

The correction function accepts only frozen scenario recipes, original labels and original opportunity frames. It derives the complete amendment set before opening canonical reports. It examines all 320 full-reference correctness cells and identifies 18 missing cap annotations and 68 event_key frames. Observed outcomes are used only afterward to evaluate corrected expectations.

## Exact category-cap corrections

Each cell below originally declared `expected_category_caps = {}`. Corrections follow C1/C2: 14 leakage cells and four inference_mismatch cells. The existing quality caps in the two k3 representation cells are preserved. A category cap is separate from a hard gate; original gates, scores and reports are unchanged. These 18 corrections add no Finding opportunities.

| Scenario ID | Old annotation | Corrected annotation | Contract-derived uncapped penalty | Basis |
| --- | --- | --- | --- | --- |
| [composite.leak_inference.n10000.csv](../candidate/scenarios/composite.leak_inference.n10000.csv.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [composite.leak_inference.n10000.pqstr](../candidate/scenarios/composite.leak_inference.n10000.pqstr.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [composite.leak_missing.n10000.csv](../candidate/scenarios/composite.leak_missing.n10000.csv.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [composite.leak_missing.n10000.pqstr](../candidate/scenarios/composite.leak_missing.n10000.pqstr.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [inference.analytics.empty.n10000.csv](../candidate/scenarios/inference.analytics.empty.n10000.csv.json) | `{}` | `{"inference_mismatch":40.0}` | inference_mismatch: 8 Finding(s), confidence .99, penalty 288.288 | C1, C2 |
| [inference.analytics.empty.n10000.pqstr](../candidate/scenarios/inference.analytics.empty.n10000.pqstr.json) | `{}` | `{"inference_mismatch":40.0}` | inference_mismatch: 8 Finding(s), confidence .99, penalty 288.288 | C1, C2 |
| [inference.analytics.omit_two.n10000.csv](../candidate/scenarios/inference.analytics.omit_two.n10000.csv.json) | `{}` | `{"inference_mismatch":40.0}` | inference_mismatch: 2 Finding(s), confidence .99, penalty 72.072 | C1, C2 |
| [inference.analytics.omit_two.n10000.pqstr](../candidate/scenarios/inference.analytics.omit_two.n10000.pqstr.json) | `{}` | `{"inference_mismatch":40.0}` | inference_mismatch: 2 Finding(s), confidence .99, penalty 72.072 | C1, C2 |
| [leak.control.numeric_normalization.n10000.csv](../candidate/scenarios/leak.control.numeric_normalization.n10000.csv.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [leak.control.numeric_normalization.n10000.pqstr](../candidate/scenarios/leak.control.numeric_normalization.n10000.pqstr.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [leak.control.support200.csv](../candidate/scenarios/leak.control.support200.csv.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.92, penalty 41.216 | C1, C2 |
| [leak.control.support200.pqstr](../candidate/scenarios/leak.control.support200.pqstr.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.92, penalty 41.216 | C1, C2 |
| [leak.equality.m10000.n10000.csv](../candidate/scenarios/leak.equality.m10000.n10000.csv.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [leak.equality.m10000.n10000.pqstr](../candidate/scenarios/leak.equality.m10000.n10000.pqstr.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [leak.equality.m9990.n10000.csv](../candidate/scenarios/leak.equality.m9990.n10000.csv.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [leak.equality.m9990.n10000.pqstr](../candidate/scenarios/leak.equality.m9990.n10000.pqstr.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [leak.equality.m9991.n10000.csv](../candidate/scenarios/leak.equality.m9991.n10000.csv.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |
| [leak.equality.m9991.n10000.pqstr](../candidate/scenarios/leak.equality.m9991.n10000.pqstr.json) | `{}` | `{"leakage":40.0}` | leakage: 1 Finding(s), confidence 0.97, penalty 43.456 | C1, C2 |

One CRITICAL equality-leakage Finding has weighted penalty 1.6 × 28 × 0.97 = 43.456; at support 200 it is 1.6 × 28 × 0.92 = 41.216. Both exceed 40. Inference metadata confidence 0.99 gives 36.036 per CRITICAL Finding: two missing features sum to 72.072, eight to 288.288, each requiring category cap 40. Single reciprocal-mapping leakage at confidence 0.88 remains below 40 and receives no new cap annotation.

## event_key: pinned contract and adverse practical specificity

There are **68 representation cells, comprising 34 logical CSV/pqstr case pairs**. Each gains exactly `schema.parse_failures::column:event_key`, severity HIGH, full counter population, and one positive check/subject-specific normative opportunity. Its optional confidence expectation remains unset, consistent with the existing annotation style. The global absent-check entry for schema.parse_failures is removed in 66 cells. In the two multicategory cells the check was already expected on signal_x; that expectation is preserved and the event_key subject is added. Other expectations, including exact split Findings and suppression, remain unchanged.

Pinned-contract interpretation: C3/C4 require this Finding under the existing date-name heuristic even though the report infers the column as text. Practical interpretation: the source values are legitimate non-null identifier strings `event_<integer>`, not physically malformed datetime values. **HIGH datetime parse warnings on valid identifiers remain ADVERSE practical Alpha specificity behavior.** Normative detection of this heuristic is not a new physical TP and is not a favorable user-facing outcome.

A fresh read-only audit verifies all values in these 68 correctness sources, plus eight related sampling sources, as legitimate identifiers. Every correctness event_key Finding retains HIGH severity, confidence 0.62 and 10,000 attempts/failures. Its isolated schema penalty is 10.04; keyed-duplicate controls and otherwise quiet group cases consequently start at readiness 90 and report confidence 81. For example, key excess 0 or 9 has readiness 90, 10 or 11 has 80, and 100 or 101 has 73. Absolute scores include this unchanged background warning. Within-family transitions describe the existing inputs, not counterfactual nuisance-free scores. Composites retain other penalties and remediation; no target score is recalculated.

The [practical-specificity record](practical_event_key.json) retains all 68 original Findings, report/source hashes, readiness, total risk, schema risk and explicit false primary-clean eligibility. Readiness across these cells ranges from 36 to 90. This paired inventory gives both affected IDs and original report links.

| Logical case | CSV cell / report | pqstr cell / report | Readiness CSV / pqstr |
| --- | --- | --- | --- |
| `composite.duplicates_group_group.n10000` | [composite.duplicates_group_group.n10000.csv](../candidate/scenarios/composite.duplicates_group_group.n10000.csv.json); [report; SHA ceac09a79704](../candidate/reports/run-76bc2c66d94f7833d2e7d8634ee1c10746eae5ffcac7841391fff2231dfbc621.json) | [composite.duplicates_group_group.n10000.pqstr](../candidate/scenarios/composite.duplicates_group_group.n10000.pqstr.json); [report; SHA ceac09a79704](../candidate/reports/run-01fc2cc70519fae28e3a47cba30793ea2f877f03d13eeb50770eac9bce153658.json) | 55 / 55 |
| `composite.duplicates_group_random.n10000` | [composite.duplicates_group_random.n10000.csv](../candidate/scenarios/composite.duplicates_group_random.n10000.csv.json); [report; SHA 900c73410171](../candidate/reports/run-de85897a3220cae12f6842a12c92efab7b63e830f32157c2c3b16384a74693a0.json) | [composite.duplicates_group_random.n10000.pqstr](../candidate/scenarios/composite.duplicates_group_random.n10000.pqstr.json); [report; SHA 900c73410171](../candidate/reports/run-9ba24fd909ee75765101915960e001777f5cc9287fc711062a4e332d4699774e.json) | 36 / 36 |
| `composite.multicategory.n10000` | [composite.multicategory.n10000.csv](../candidate/scenarios/composite.multicategory.n10000.csv.json); [report; SHA 4ce59a739296](../candidate/reports/run-cd512884842f0bec8e6396f64972d81f84376732c877c20afa01709773b5773a.json) | [composite.multicategory.n10000.pqstr](../candidate/scenarios/composite.multicategory.n10000.pqstr.json); [report; SHA a96976a2e2f7](../candidate/reports/run-34c83bf0539e927905d489e8f1e1c4cfe17e17d0bbccf8605b60dce1e347a47c.json) | 54 / 54 |
| `duplicate.keys.e0.n10000` | [duplicate.keys.e0.n10000.csv](../candidate/scenarios/duplicate.keys.e0.n10000.csv.json); [report; SHA 5b3f43f93267](../candidate/reports/run-6605483ef232b418369489a365a81d6f4920d33549e24e38e7eae0285f69e827.json) | [duplicate.keys.e0.n10000.pqstr](../candidate/scenarios/duplicate.keys.e0.n10000.pqstr.json); [report; SHA 5b3f43f93267](../candidate/reports/run-06aafe15518202bc23ec7aea9d3f498c086dd9a62f8752854db4c015f32aca80.json) | 90 / 90 |
| `duplicate.keys.e10.n10000` | [duplicate.keys.e10.n10000.csv](../candidate/scenarios/duplicate.keys.e10.n10000.csv.json); [report; SHA 9a743860eb53](../candidate/reports/run-545563b47000aa76a12a1df14fb1e80adccc05e771051cc85cef2c5c0efc711a.json) | [duplicate.keys.e10.n10000.pqstr](../candidate/scenarios/duplicate.keys.e10.n10000.pqstr.json); [report; SHA 9a743860eb53](../candidate/reports/run-e082b3f0a46057ba90179b1b2b4a3028fe4b09e3381b12abd0178b0476858b40.json) | 80 / 80 |
| `duplicate.keys.e100.n10000` | [duplicate.keys.e100.n10000.csv](../candidate/scenarios/duplicate.keys.e100.n10000.csv.json); [report; SHA 56f2229a8d01](../candidate/reports/run-c156450b7f296a81e137be3b1dd3b86a7155d0ee0b89787045d08f4b71d71920.json) | [duplicate.keys.e100.n10000.pqstr](../candidate/scenarios/duplicate.keys.e100.n10000.pqstr.json); [report; SHA 56f2229a8d01](../candidate/reports/run-ab5b41e0a3e0fe3fbf52f078de3c54e7ba462311c9fb632d6c440a39176c092b.json) | 73 / 73 |
| `duplicate.keys.e101.n10000` | [duplicate.keys.e101.n10000.csv](../candidate/scenarios/duplicate.keys.e101.n10000.csv.json); [report; SHA ebb86142fae5](../candidate/reports/run-c2bdb125d3444c7f89be89882c8005e07f24d0cc8f709a0c24bb485fb5726c9b.json) | [duplicate.keys.e101.n10000.pqstr](../candidate/scenarios/duplicate.keys.e101.n10000.pqstr.json); [report; SHA ebb86142fae5](../candidate/reports/run-e08da2e08433ef401cbe557e47cb397135cfa21345ab7ddca766cd661adcb326.json) | 73 / 73 |
| `duplicate.keys.e11.n10000` | [duplicate.keys.e11.n10000.csv](../candidate/scenarios/duplicate.keys.e11.n10000.csv.json); [report; SHA 91774c50d008](../candidate/reports/run-389075341871e3fbf6f657c4d3917b5d39c83a89f573841acd87d7bcb25efa55.json) | [duplicate.keys.e11.n10000.pqstr](../candidate/scenarios/duplicate.keys.e11.n10000.pqstr.json); [report; SHA 91774c50d008](../candidate/reports/run-be85ca55502e326b48e40c72480059ae26bd62e3f7df90f69a6f7ccd13a7339d.json) | 80 / 80 |
| `duplicate.keys.e9.n10000` | [duplicate.keys.e9.n10000.csv](../candidate/scenarios/duplicate.keys.e9.n10000.csv.json); [report; SHA d07c7502bf64](../candidate/reports/run-62251173043fb1f56324eefe1dfec5f43a7d6a76e90027f3b13a330cb32ce8f0.json) | [duplicate.keys.e9.n10000.pqstr](../candidate/scenarios/duplicate.keys.e9.n10000.pqstr.json); [report; SHA d07c7502bf64](../candidate/reports/run-864dc70e2d5311495d5d949f2cbd305b4b76de919e084b70a3745e2d26b1688d.json) | 90 / 90 |
| `duplicate.keys.e99.n10000` | [duplicate.keys.e99.n10000.csv](../candidate/scenarios/duplicate.keys.e99.n10000.csv.json); [report; SHA 523a9b74c98b](../candidate/reports/run-3006b603b44e808ab8f8a7727b776fc8952683bca41a7833ae68dd108fa3704e.json) | [duplicate.keys.e99.n10000.pqstr](../candidate/scenarios/duplicate.keys.e99.n10000.pqstr.json); [report; SHA 523a9b74c98b](../candidate/reports/run-1152dc13608cd40d1dd9181a520c512207d6f9d42ffa904622d1f7d19e769130.json) | 80 / 80 |
| `group.group.r0.n10000` | [group.group.r0.n10000.csv](../candidate/scenarios/group.group.r0.n10000.csv.json); [report; SHA f6ced00d9451](../candidate/reports/run-ab99ac242d95335a12ee74f26c27ca7487fa0593632be9c051623294f6edcf70.json) | [group.group.r0.n10000.pqstr](../candidate/scenarios/group.group.r0.n10000.pqstr.json); [report; SHA f6ced00d9451](../candidate/reports/run-a555748cc59b7c433da29b533f59d806517a12d82285bc6d5487a3829cf53fa4.json) | 90 / 90 |
| `group.group.r1999.n10000` | [group.group.r1999.n10000.csv](../candidate/scenarios/group.group.r1999.n10000.csv.json); [report; SHA 45426cde5613](../candidate/reports/run-98a899d1454efc85680a709ad97e110ce7df7ae3f6a51a7cd8118a6dcfeb9cd9.json) | [group.group.r1999.n10000.pqstr](../candidate/scenarios/group.group.r1999.n10000.pqstr.json); [report; SHA 45426cde5613](../candidate/reports/run-31598bcbc653761d97b10582bc7e42a4730e53bb88ffd284ba7f825703d07602.json) | 90 / 90 |
| `group.group.r2000.n10000` | [group.group.r2000.n10000.csv](../candidate/scenarios/group.group.r2000.n10000.csv.json); [report; SHA 584846699ab7](../candidate/reports/run-f0316e95e1156e5ec363346421693eb9df1a8c2e4d4d7fcace99202e496d9e15.json) | [group.group.r2000.n10000.pqstr](../candidate/scenarios/group.group.r2000.n10000.pqstr.json); [report; SHA 584846699ab7](../candidate/reports/run-33503c53c2e80895c464516593b24652f9b62963b8f918248f9ee005e7e24b62.json) | 90 / 90 |
| `group.group.r2001.n10000` | [group.group.r2001.n10000.csv](../candidate/scenarios/group.group.r2001.n10000.csv.json); [report; SHA 229cde656430](../candidate/reports/run-4c7e966dc634cc17671f512cd5281ee5f0153f72675c4243de4ab82b05443f49.json) | [group.group.r2001.n10000.pqstr](../candidate/scenarios/group.group.r2001.n10000.pqstr.json); [report; SHA 229cde656430](../candidate/reports/run-8b883dd6bc8567c072a83d17147351dbf176ae4f976916820d17d20b74722c4a.json) | 90 / 90 |
| `group.group.r499.n10000` | [group.group.r499.n10000.csv](../candidate/scenarios/group.group.r499.n10000.csv.json); [report; SHA ffce9fc3a311](../candidate/reports/run-fc9105d8019c6479316fd504c1920b85fa188fd589380d8b5269aeedf11f8b26.json) | [group.group.r499.n10000.pqstr](../candidate/scenarios/group.group.r499.n10000.pqstr.json); [report; SHA ffce9fc3a311](../candidate/reports/run-8a40bd3ee5ab16ac13b3bd0b9b9b3158a547b713dec32b059c04d83aa3b5cc1d.json) | 90 / 90 |
| `group.group.r500.n10000` | [group.group.r500.n10000.csv](../candidate/scenarios/group.group.r500.n10000.csv.json); [report; SHA 2518cd70752b](../candidate/reports/run-158c71b7961eb9df41e02e9255ed01fecd725206763b1196f3eff58adc25fb53.json) | [group.group.r500.n10000.pqstr](../candidate/scenarios/group.group.r500.n10000.pqstr.json); [report; SHA 2518cd70752b](../candidate/reports/run-8bfa75fe6886503b1ab1038dae6a45c8ca94a017a1ee6e9c74d9b6706e17b58d.json) | 90 / 90 |
| `group.group.r501.n10000` | [group.group.r501.n10000.csv](../candidate/scenarios/group.group.r501.n10000.csv.json); [report; SHA 600c2ecd0193](../candidate/reports/run-3e9328b8efc647938cc4e0d31399e136669a1b35dcb927d35415e7072c48d214.json) | [group.group.r501.n10000.pqstr](../candidate/scenarios/group.group.r501.n10000.pqstr.json); [report; SHA 600c2ecd0193](../candidate/reports/run-00c15a7d22a9125bce954fa0f58b4aa679e916ea5e34438eeca52f1e46a6ef44.json) | 90 / 90 |
| `group.random.r0.n10000` | [group.random.r0.n10000.csv](../candidate/scenarios/group.random.r0.n10000.csv.json); [report; SHA f6ced00d9451](../candidate/reports/run-ddbd4fd9d1f29455ddd6a00b6ac31b282ef552be00ecd2e2a2a3fc90eaf50480.json) | [group.random.r0.n10000.pqstr](../candidate/scenarios/group.random.r0.n10000.pqstr.json); [report; SHA f6ced00d9451](../candidate/reports/run-d38380081bc7a58c7317e797fd0dbcd086dfdb9d93a8d686c0edbd6e595b8006.json) | 90 / 90 |
| `group.random.r1999.n10000` | [group.random.r1999.n10000.csv](../candidate/scenarios/group.random.r1999.n10000.csv.json); [report; SHA 80af8f08006a](../candidate/reports/run-9e43a67c503e3ac97da034b9bc1cfae6615324c0d9c54206616219b6fd89df78.json) | [group.random.r1999.n10000.pqstr](../candidate/scenarios/group.random.r1999.n10000.pqstr.json); [report; SHA 80af8f08006a](../candidate/reports/run-a8c9a93cf13022becc47f171061712c093f4368f6674fa35355b76743a023c77.json) | 79 / 79 |
| `group.random.r2000.n10000` | [group.random.r2000.n10000.csv](../candidate/scenarios/group.random.r2000.n10000.csv.json); [report; SHA e2fbfbeaeabd](../candidate/reports/run-f3193bd5f888710efa91dc37eafc2e9d427a77d9f2c43499b8bc538f42770b54.json) | [group.random.r2000.n10000.pqstr](../candidate/scenarios/group.random.r2000.n10000.pqstr.json); [report; SHA e2fbfbeaeabd](../candidate/reports/run-c845dc45931811a996b600715d030747d0f1ad95e3d94c7fb07eb99fb6943b9e.json) | 71 / 71 |
| `group.random.r2001.n10000` | [group.random.r2001.n10000.csv](../candidate/scenarios/group.random.r2001.n10000.csv.json); [report; SHA 9e83f283c58b](../candidate/reports/run-d510b52131d3312e8372a1e3d2a4fa7d914a1b13bb892d9cbc9d915548df78bb.json) | [group.random.r2001.n10000.pqstr](../candidate/scenarios/group.random.r2001.n10000.pqstr.json); [report; SHA 9e83f283c58b](../candidate/reports/run-ba0ab45956320524f7ef72c84880bdbcde94ea1ef7e90a402b2391c681addfbf.json) | 71 / 71 |
| `group.random.r499.n10000` | [group.random.r499.n10000.csv](../candidate/scenarios/group.random.r499.n10000.csv.json); [report; SHA ffce9fc3a311](../candidate/reports/run-f0f8fbd0fb446a92814b095cd2ba1441caa64dc871f2f15c63c672b826674a33.json) | [group.random.r499.n10000.pqstr](../candidate/scenarios/group.random.r499.n10000.pqstr.json); [report; SHA ffce9fc3a311](../candidate/reports/run-b90d977f2833fe77c2814afc3b5adc81d16f21cd4d698fd269ee23309d7594ee.json) | 90 / 90 |
| `group.random.r500.n10000` | [group.random.r500.n10000.csv](../candidate/scenarios/group.random.r500.n10000.csv.json); [report; SHA 1b723b184435](../candidate/reports/run-f9c4073512c1d10fd329aa3b8b87cca1f059048a18fd323655d5935fd4eafc32.json) | [group.random.r500.n10000.pqstr](../candidate/scenarios/group.random.r500.n10000.pqstr.json); [report; SHA 1b723b184435](../candidate/reports/run-ef588bf746b03010e3147531702ffb79c2bb70c7565b350403403eeef34bfa96.json) | 79 / 79 |
| `group.random.r501.n10000` | [group.random.r501.n10000.csv](../candidate/scenarios/group.random.r501.n10000.csv.json); [report; SHA 4cd6f744f2af](../candidate/reports/run-0aa40d6601899b2a537d9c25d5e77c4c13fb60dba2997faf71819842c7ecd577.json) | [group.random.r501.n10000.pqstr](../candidate/scenarios/group.random.r501.n10000.pqstr.json); [report; SHA 4cd6f744f2af](../candidate/reports/run-6105df7a35d2763f0ee44d237ff1b628c2464fe62c4401af8a1a6f92558cd17d.json) | 79 / 79 |
| `group.time.r0.n10000` | [group.time.r0.n10000.csv](../candidate/scenarios/group.time.r0.n10000.csv.json); [report; SHA f6ced00d9451](../candidate/reports/run-2b80a3d6445b50b363d2fc3f605d01607c71b9802b1089569c63e1a28062d4d1.json) | [group.time.r0.n10000.pqstr](../candidate/scenarios/group.time.r0.n10000.pqstr.json); [report; SHA f6ced00d9451](../candidate/reports/run-05b8adf7fc014b771570bcb2baf3127f382b27787ebd1c1c09411b6e6c139770.json) | 90 / 90 |
| `group.time.r1999.n10000` | [group.time.r1999.n10000.csv](../candidate/scenarios/group.time.r1999.n10000.csv.json); [report; SHA 36f9e8ca8737](../candidate/reports/run-1709164230ef9998b046bf35356b435f8022dfd26e79a94f5c03bb1a0a5e034a.json) | [group.time.r1999.n10000.pqstr](../candidate/scenarios/group.time.r1999.n10000.pqstr.json); [report; SHA 36f9e8ca8737](../candidate/reports/run-cbcc367187818b0c62abb2c4c3062a90882ace619d5a8fa205b4ca78eb5daa60.json) | 79 / 79 |
| `group.time.r2000.n10000` | [group.time.r2000.n10000.csv](../candidate/scenarios/group.time.r2000.n10000.csv.json); [report; SHA 5c4dbf15f885](../candidate/reports/run-fb13a176edecddba0ccb0a23314a97c629b080e2eb6d087727367af884cc8ab1.json) | [group.time.r2000.n10000.pqstr](../candidate/scenarios/group.time.r2000.n10000.pqstr.json); [report; SHA 5c4dbf15f885](../candidate/reports/run-0d93956e0dc500cba57f34528564c0e011416c34bc615e30e82760d77a00d782.json) | 71 / 71 |
| `group.time.r2001.n10000` | [group.time.r2001.n10000.csv](../candidate/scenarios/group.time.r2001.n10000.csv.json); [report; SHA 29facfe63e22](../candidate/reports/run-334423c884e9326768f0669df59dcc8dec907034f7801253099409b3f36e4e48.json) | [group.time.r2001.n10000.pqstr](../candidate/scenarios/group.time.r2001.n10000.pqstr.json); [report; SHA 29facfe63e22](../candidate/reports/run-e23129c849113609f7ac83ad7b6c773a1564f58d691e87a1eb2161cf4a25d0cd.json) | 71 / 71 |
| `group.time.r499.n10000` | [group.time.r499.n10000.csv](../candidate/scenarios/group.time.r499.n10000.csv.json); [report; SHA ffce9fc3a311](../candidate/reports/run-c1066d9fc176bd075bd23e93de6f08d72d919d1664ce090a8dcd6b207b0963ef.json) | [group.time.r499.n10000.pqstr](../candidate/scenarios/group.time.r499.n10000.pqstr.json); [report; SHA ffce9fc3a311](../candidate/reports/run-e4cdabdb3337e6d74218952f1314ca0913a7a7de44a09f49e0fca0ae2c4b50e9.json) | 90 / 90 |
| `group.time.r500.n10000` | [group.time.r500.n10000.csv](../candidate/scenarios/group.time.r500.n10000.csv.json); [report; SHA a012a8be0d2d](../candidate/reports/run-d5f8f29e7dac168b4f81f4f3011c32ef95aeadba9bce4721564536eb6541a116.json) | [group.time.r500.n10000.pqstr](../candidate/scenarios/group.time.r500.n10000.pqstr.json); [report; SHA a012a8be0d2d](../candidate/reports/run-451143d4870ebf0d2f55e41021578a7783493b8584a4df672d70a3abd2cbd9f1.json) | 79 / 79 |
| `group.time.r501.n10000` | [group.time.r501.n10000.csv](../candidate/scenarios/group.time.r501.n10000.csv.json); [report; SHA bd218cf9b939](../candidate/reports/run-78379141d6a8c9596b6ca394844f63bce5e84d3f59b261f931451ef9035e9582.json) | [group.time.r501.n10000.pqstr](../candidate/scenarios/group.time.r501.n10000.pqstr.json); [report; SHA bd218cf9b939](../candidate/reports/run-d5e45cc4d6ce1ea70818efe02b0206bf5330d43a2d54c9447e6bfe62c7af58cb.json) | 79 / 79 |
| `inference.analytics.roles_only_excluded.n10000` | [inference.analytics.roles_only_excluded.n10000.csv](../candidate/scenarios/inference.analytics.roles_only_excluded.n10000.csv.json); [report; SHA 5b3f43f93267](../candidate/reports/run-e0aca10476a5f537828ea2578e7cf58d95136d6af65e6c18023d980af9c89ca8.json) | [inference.analytics.roles_only_excluded.n10000.pqstr](../candidate/scenarios/inference.analytics.roles_only_excluded.n10000.pqstr.json); [report; SHA 5b3f43f93267](../candidate/reports/run-d7ecf5c297ea72646474c320e857afcc0c0c52fa99ae4e1866fc4dd81e0e66ae.json) | 90 / 90 |
| `negative.analytics_entity.n10000` | [negative.analytics_entity.n10000.csv](../candidate/scenarios/negative.analytics_entity.n10000.csv.json); [report; SHA 33e09b4bb9f8](../candidate/reports/run-53fed9115db743fa6aa62b6d2488922b93875a83769f7a51c020551c02fd261a.json) | [negative.analytics_entity.n10000.pqstr](../candidate/scenarios/negative.analytics_entity.n10000.pqstr.json); [report; SHA 33e09b4bb9f8](../candidate/reports/run-e42019da9228cc5992349f2fbe77d35dbdf5f56438299fc676594dcb72d3bd65.json) | 90 / 90 |
| `split.ts_group.n10000` | [split.ts_group.n10000.csv](../candidate/scenarios/split.ts_group.n10000.csv.json); [report; SHA 884ef9f3e3f2](../candidate/reports/run-401cc0637aa2ee340f52300d454287fdff6f8b6ebb9d817d2dd9b2689ff074bf.json) | [split.ts_group.n10000.pqstr](../candidate/scenarios/split.ts_group.n10000.pqstr.json); [report; SHA 884ef9f3e3f2](../candidate/reports/run-2f3544ccef4242f50bcd5d5a17308bf75cef3e0ab50ec68345235ae8c640bf32.json) | 69 / 69 |

The primary-clean frame remains eight preregistered controls and 226 negative opportunities: FPR 0/226 and 0/8 affected controls. None of the 68 event_key cells is added post hoc. The eight separate registered specificity challenges retain their original frame: six expected INFO identifier Findings, physical INFO FPR 6/216 and LOW-or-higher 0/216. Zero primary-clean or fixed-frame normative FPR does not establish zero practical false alarms on other valid schema shapes.

## ORIGINAL PREREGISTERED-LABEL RESULT versus ADJUDICATED PINNED-CONTRACT RESULT

Whole-cell conformance uses one standard-context, repeat-0, full-reference correctness report per cell: 320 cells, 160 per representation. Other repeats, sampling arms, scale measurements and diagnostics do not enlarge this denominator. The original 86 failures comprise 68 event_key frame disagreements and 18 cap-label defects. The adjudicated value uses the existing evaluator, including Finding matching, absent behavior, out-of-frame behavior, severity, original explicit confidence labels, exact hard gates, category caps and suppression.

| Metric | ORIGINAL PREREGISTERED-LABEL RESULT | ADJUDICATED PINNED-CONTRACT RESULT |
| --- | --- | --- |
| Whole-cell normative conformance | 234/320 (73.1250%) | 320/320 (100.0000%) |
| Exact category-cap correctness | 302/320 (94.3750%) | 320/320 (100.0000%) |
| Exact hard-gate set correctness | 320/320 (100.0000%) | 320/320 (100.0000%) |
| Readiness respects hard gates | 320/320 (100.0000%) | 320/320 (100.0000%) |
| Explicit suppression opportunities | 8/8 (100.0000%) | 8/8 (100.0000%) |
| Normatively positive scenario detection | 206/206 (100.0000%) | 236/236 (100.0000%) |
| All required normative Findings in a positive scenario | 206/206 (100.0000%) | 236/236 (100.0000%) |
| Out-of-frame Finding occurrences | 68 | 0 |
| Independent expected Finding matches | 252/252 | 320/320 |
| Independent severity matches | 252/252 | 320/320 |
| Independent original explicit confidence labels | 6/6 | 6/6 |
| Independent positive gate occurrences | 50/50 | 50/50 |
| Independent suppression | 8/8 | 8/8 |

Independent counts use exact check/subject matches and original report severities and gate fields, not stored success labels. Unexpected gate occurrences remain 0. Three disposable software counterexamples confirm that removing the new expected Finding, lowering its severity, or removing a required category cap each fails conformance. Those copies are never saved as scientific evidence and cause no target calls.

| Label set / cutoff | TP | FP | FN | TN | Positive opportunities | Total coverage | Severity correctness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Original / INFO | 252 | 0 | 0 | 8854 | 252 | 9106/9106 (100.0000%) | 252/252 (100.0000%) |
| Original / LOW | 246 | 0 | 0 | 8860 | 246 | 9106/9106 (100.0000%) | 246/246 (100.0000%) |
| Adjudicated / INFO | 320 | 0 | 0 | 8854 | 320 | 9174/9174 (100.0000%) | 320/320 (100.0000%) |
| Adjudicated / LOW | 314 | 0 | 0 | 8860 | 314 | 9174/9174 (100.0000%) | 314/314 (100.0000%) |

The correction adds 68 normative positive opportunities and removes no normative negative opportunities: total coverage denominator moves from 9,106 to 9,174. Cap corrections change whole-cell conformance without changing opportunities. These are openly adjudicated denominators, never presented as the original preregistered frame. At INFO, expected-Finding precision/recall become 320/320 and negative-opportunity FPR remains 0/8854. At LOW, six original INFO expectations are excluded from positive support; all 68 HIGH event_key expectations remain. The [machine-readable summary](summary.json) retains both cutoffs and each representation separately.

## Preserved physical metrics and unfavorable observations

Physical truth, detector mappings, opportunity IDs, strata and primary-clean eligibility are unchanged. The approved shared-entity OR counts one physical opportunity while check-specific normative expectations and suppression remain separate. No malformed-datetime physical truth for event_key is invented.

| Physical cutoff | TP | FP | FN | TN | Detection / positives | FPR / negatives | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| INFO | 246 | 6 | 68 | 8716 | 246/314 (78.3439%) | 6/8722 (0.0688%) | 9036/9036 (100.0000%) |
| LOW | 246 | 0 | 68 | 8722 | 246/314 (78.3439%) | 0/8722 (0.0000%) | 9036/9036 (100.0000%) |

Physical detection remains 246/314 and all 68 physical misses remain. These misses are distinct from the coincidentally equal count of 68 event_key warning cells. Below-threshold defects, collapsed or insufficient support, nonreciprocal leakage, allowlisting and group-split policy/applicability retain their original strata. Physical positive-scenario detection remains 200/260 and all-required detection 192/260. Complete coverage makes end-to-end physical yield numerically equal conditional recall here; definitions remain separate.

The [original scientific review](../../ALPHA_BENCHMARK_V1_SCIENTIFIC_RESULT_REVIEW.md) remains the detailed immutable record of every physical miss, all eight sampling disagreements, all 42 format mismatches, determinism pairs, score boundaries and performance observations. Only its V1 normative-label conclusion is superseded by this overlay. Its adverse evidence and original 234/320 result remain preserved.

Sampling retains 36 reference/bounded pairs and 72 diagnostics: 28 exact Finding-set agreements and eight disagreements. The sample remains the fixed HEAD_STRIDE_V1 geometry; exact repetition does not remove its blind spots.

| Existing sampling disagreement | Full-reference to bounded observation, unchanged |
| --- | --- |
| cardinality.head | Distinct share 0.98 to 0.97; LOW warning disappears; readiness 97 to 100 |
| class_boundary.middle | Minority share 0.10 to 0.09; MEDIUM warning appears; readiness 100 to 92 |
| class_boundary.tail | Minority share 0.10 to 0.09; MEDIUM warning appears; readiness 100 to 92 |
| class_rare.gaps | Rare class absent from sample; HIGH warning disappears; readiness 83 to 100 |
| duplicate_keys.gaps | Duplicate destinations outside sample; duplicate warning disappears; event_key persists; readiness 73 to 90 |
| duplicate_rows.gaps | Duplicate destinations outside sample; MEDIUM warning disappears; readiness 90 to 100 |
| group.gaps | Repeated-entity participants disappear; recommendation disappears; event_key persists; readiness 79 to 90 |
| leakage.head | Agreement share 0.999 to 0.9985; CRITICAL leakage and hard gate disappear; readiness 60 to 100 |

The leakage 60 to 100 change remains a negative sampling result, not improved underlying data. Full-scan missingness/parse counters retain invariance across their eight pairs. The class_rare diagnostic counts the smallest observed class, not the injected class with zero sampled members. Primitive availability and all diagnostics are unchanged.

Strict format comparisons retain 37 mismatches among 160 CSV/pqstr pairs and five among five eligible native projections: 42 total. String-transport mismatches concern empty-token versus typed-null string statistics; native mismatches retain string_stats differences for typed values. All paired Findings, readiness, total/category risks, confidence, gates/caps, analysis_stats and remediation agree. The original strict comparison is not replaced by a more favorable normalized metric. This is V3, a publication caveat rather than inconsistent risk decisions.

Determinism retains 72 within-context repeat pairs with identical canonical bytes/hashes and 159/159 table comparisons (132 context comparisons plus 27 scale comparisons), supporting only tested cases/repeats/contexts. Parser/scoring non-monotonicity remains: numeric corruption 2000/10000 gives readiness 89 and Finding confidence 0.70; 4000/10000 gives readiness 90 and confidence 0.62; 6000/10000 loses numeric dominance and gives readiness 100. Readiness and confidence are not calibrated or monotonic physical-damage measures. A collapsed class can also escape the diversity-dependent imbalance check. Remediation gains remain heuristic estimates, not measured causal recovery.

Performance retains 13 regular-scale cells with three measurements each, the 5M cell with two measurements, and 13 excluded warmups. 5M times remain 914.052132966 and 910.409173628 seconds, median 912.230653297; n=2 is weak descriptive evidence only. The 1M width-100 native median remains 1148.830717559 seconds. Fixed sampled P does not eliminate full-scan/input costs or make modes equal work. All 578 monitors remain complete; requested RSS interval is 0.01 seconds and the maximum observed gap is 0.105340397 seconds. RSS is a sampled worker-tree sum excluding the supervisor, includes worker baseline memory, and can miss brief peaks. One prepared WSL2/ext4 environment is not a native-Linux replication, cold-cache experiment, production bound or general hardware comparison.

## Evidence preservation and validation

The [preservation record](evidence_preservation.json) retains all 1,062 original candidate file hashes before and after processing; inventories match. Fresh read-only verification matches 370 original source files, 578 ledger reports and 72 original diagnostics to the candidate. All 15 original evidence-derived tables are regenerated in memory using existing query code and match their CSV bytes. Original figures, report, receipts, RunSpecs, scenario/expectation snapshots, diagnostics, attempts and instrumentation remain intact.

| Integrity binding | Unchanged SHA-256 |
| --- | --- |
| Candidate checksum manifest | `6bfde18953a2a822218f1ad31f3e007ad809526e188374daf2b8ddc6daf1d498` |
| Report-hash inventory | `616e5ed9c4109f6dece3416512cb7438a10c958daf1301439b43f107bfb91cc2` |
| Source-hash inventory | `51061bcc373e296d94b10ddd69ecce337083365f22a0c4b3a35521504d16c1a5` |
| Attempt ledger | `a1e8b7937b337ec197d9f22df748bd9ddd034442768b5595dcf21908166f3677` |
| Instrumentation | `2ff2b5ff83cc6d90d8b27551433738af272ae689b1353ec33648db0c560ee7e0` |
| Original scientific review | `7849d206afd5ae3141044e72cb2275dd6f427f643341174ec8ed8a18e3f0b202` |

Checks cover typed annotations/opportunities, design-only derivation, independent Finding/severity/gate/suppression evaluation, three negative software controls, unchanged physical frames/metrics at both cutoffs and representations, source/report/diagnostic/ledger hashes, byte-identical sampling/determinism/performance/clean tables, deterministic supplemental serialization and the repository public-safety scanner. An explicit import guard forbids target imports. No target code, primary RunSpec, diagnostic TADR call or scientific worker was executed. No scientific fixture was regenerated.

Only ignored review/adjudication artifacts were written. Benchmark tracked files and tadr-core are unchanged; no commit was created. Campaign status, public RESULTS.md and the candidate are unchanged. No figures or frozen results were generated.

## Remaining validity findings and freeze eligibility

| ID | Status / severity | Disposition |
| --- | --- | --- |
| V1 | Resolved by approved adjudication | C1/C2 justify 18 missing caps; C3/C4 justify 68 event_key frames from the pre-execution contract. Original labels and 234/320 are retained; corrected conformance is recomputed from immutable evidence. |
| V2 | IMPORTANT | Valid event_key identifiers trigger HIGH datetime advice and lower absolute readiness in keyed/group and related families. Retain as adverse specificity; qualify primary-clean FPR and scores. No physical or clean denominator change. |
| V3 | IMPORTANT | Retain 42 strict format mismatches and profile-statistic causes while stating that decision fields agree. Do not substitute a post hoc normalized comparison. |
| V4 | MINOR | Permanent docs still include design-time PLANNED/deferred wording; READY source manifest is a launch declaration. Distinguish that history from the completed private candidate before public release. Public status/RESULTS changes are outside this pass. |

V2/V3 remain publication caveats and V4 a documentation task. Poor physical detection, nuisance warnings, sampling blind spots and slow runtime do not themselves invalidate the benchmark. Corrected labels have a pre-execution contract basis; physical truth and scientific inputs did not change; authoritative evidence was not rewritten; no new integrity issue was found. The remaining critical-condition inventory is explicit in the machine-readable summary.

**Remaining: CRITICAL 0; IMPORTANT 2; MINOR 1.**

**READY FOR FREEZE REVIEW**

The original candidate must be accompanied by this adjudication record and explicit original-versus-adjudicated labels at any later freeze review. This pass performs no freeze, publication, commit or scientific rerun.
