"""Deterministic presentation of the approved annotation adjudication."""
import json
from collections import defaultdict
from alpha_v1_rules import CONTRACT_BASIS


def make_review(record, provenance, preservation, practical, scenarios,
                artifact_base='', candidate_base='../candidate/', history_base='../../'):
    results = record['effect_on_derived_metrics']
    before = results['original_preregistered_label_result']
    after = results['adjudicated_pinned_contract_result']
    counts = results['remaining_issues']
    def ratio(r):
        n, d = r['numerator'], r['denominator']
        return f'{n}/{d}' + (f' ({100*n/d:.4f}%)' if d else ' (undefined)')
    def j(value):
        return json.dumps(value, sort_keys=True, separators=(',', ':')).replace('|', '\\|')
    def artifact(label, name):
        return f'[{label}]({artifact_base}{name})'
    def source(sid):
        return f'[{sid}]({candidate_base}scenarios/{sid}.json)'
    def report(p):
        return f'[report; SHA {p["canonical_report_sha256"][:12]}]({candidate_base}reports/{p["run_id"]}.json)'
    lines = [
        '# ALPHA_BENCHMARK_V1 annotation adjudication review', '',
        f'**{results["verdict"]}**', '',
        f'Original whole-cell conformance is **{ratio(before["whole_cell_normative_conformance"])}**. '
        f'The approved contract-label corrections produce **{ratio(after["whole_cell_normative_conformance"])}** '
        'on the same 320 correctness reports. This value was recomputed from corrected labels and unchanged report fields; it was not used as a target for the calculation.', '',
        f'Remaining: **CRITICAL {counts["CRITICAL"]}; IMPORTANT {counts["IMPORTANT"]}; MINOR {counts["MINOR"]}**. '
        'Counts concern benchmark validity and publication interpretation, not favorable target performance. '
        'Valid-identifier parse warnings remain an adverse Alpha result. This is eligibility for freeze review; no freeze or public release occurred.', '',
        '## Evidence and processing scope', '',
        '| Binding | Value |', '| --- | --- |',
        f'| Scientific execution revision, unchanged | §{record["execution_revision"]}§ |',
        f'| Benchmark processing revision, unchanged | §{record["benchmark_processing_revision"]}§ |',
        '| Target | tadr-core 0.1.0; proprietary; Algorithm 1.0; MVP_V1; AnalysisBundle 1.0; implementation baseline 1.0.12 |',
        '| Approved wheel SHA-256 | §a37ec8d336d16dbe4b7a7448071808daaf5e3e0ab03afe3bb7de0ce6882bc31d§ |',
        '| Retained evidence | 578 selected outcomes and canonical reports; 13 warmups and 565 measured primary outcomes; 72 diagnostics; 370 source identities; original attempts and instrumentation |',
        '| Scientific environment | Ubuntu 24.04 under WSL2; Linux x86_64; Python 3.11.9; POLARS_MAX_THREADS=4; WSL-native ext4 scientific storage |',
        '| Adjudication | Deterministic benchmark-side annotation/evaluation processing; zero target imports and zero scientific invocations |', '',
        'The original candidate, annotations, scenario hashes and scientific review remain byte-for-byte intact. '
        'The correction is a supplemental processing overlay. Editing original scenario snapshots would change scientific identities; deriving new physical opportunities from the new normative subject would change the physical denominator. Neither occurred. '
        'Original runs.jsonl detection fields and original tables retain their historical evaluation and must not be presented as adjudicated values.', '',
        f'The {artifact("machine-readable adjudication", "adjudication.json")} contains every full old and corrected annotation, old and corrected normative frame, '
        'scenario identity/hash, category, justification, contract-rule references and per-cell metric effect. '
        f'The {artifact("corrected annotation overlay", "corrected_normative_annotations.json")}, '
        f'{artifact("adjudicated scenario metrics", "adjudicated_scenario_metrics.json")}, '
        f'{artifact("adjudicated scenario table", "tables/adjudicated_scenario_matrix.csv")} and '
        f'{artifact("adjudicated detection table", "tables/adjudicated_detection_by_check.csv")} accompany it. '
        'The original whole-cell result is retained permanently as annotation history.', '',
        f'The {artifact("processing provenance", "adjudication_provenance.json")} identifies supplemental operator scripts by content hash '
        'and records the actual Windows annotation-processing environment separately from Linux scientific execution. '
        'It does not claim uncommitted operator scripts belong to the existing processing commit. '
        f'The {artifact("bundle checksums", "checksums.sha256")} bind the supplemental artifacts. No benchmark, result, instrumentation, scenario or annotation version changed.', '',
        '## Pre-execution contract basis', '',
        'The rules were derived from the pre-existing Algorithm 1.0 contract in the approved wheel, not selected from observed outcomes. '
        'Static inspection and hashes bind 14 relevant module texts to that wheel; no proprietary source text or private source revision is copied here. '
        f'{artifact("Contract rules, symbols and member hashes", "contract_basis.json")} provide the exact basis.', '',
    ]
    for key, basis in CONTRACT_BASIS.items():
        lines += [f'### {key}: {basis["name"]}', '', basis['rule'], '',
                  'Members and symbols: ' + '; '.join(f'§{member}§: ' + ', '.join(f'§{s}§' for s in symbols) for member, symbols in basis['members'].items()) + '.', '']
    lines += [
        'The correction function accepts only frozen scenario recipes, original labels and original opportunity frames. '
        'It derives the complete amendment set before opening canonical reports. It examines all 320 full-reference correctness cells and identifies 18 missing cap annotations and 68 event_key frames. '
        'Observed outcomes are used only afterward to evaluate corrected expectations.', '',
        '## Exact category-cap corrections', '',
        'Each cell below originally declared §expected_category_caps = {}§. Corrections follow C1/C2: 14 leakage cells and four inference_mismatch cells. '
        'The existing quality caps in the two k3 representation cells are preserved. A category cap is separate from a hard gate; original gates, scores and reports are unchanged. '
        'These 18 corrections add no Finding opportunities.', '',
        '| Scenario ID | Old annotation | Corrected annotation | Contract-derived uncapped penalty | Basis |',
        '| --- | --- | --- | --- | --- |',
    ]
    cap_rows, event_rows = [], []
    for row in record['corrections']:
        for change in row['changes']:
            if change['category'] == 'category_cap_annotation_defect':
                cap_rows.append(row)
                derivation = '; '.join(f'{d["category"]}: {d["finding_count"]} Finding(s), confidence {d["confidence"]}, penalty {d["uncapped_penalty"]}' for d in change['derivation'])
                lines.append(f'| {source(row["scenario_id"])} | §{j(change["old"])}§ | §{j(change["corrected"])}§ | {derivation} | C1, C2 |')
            else:
                event_rows.append(row)
    lines += [
        '',
        'One CRITICAL equality-leakage Finding has weighted penalty 1.6 × 28 × 0.97 = 43.456; at support 200 it is 1.6 × 28 × 0.92 = 41.216. '
        'Both exceed 40. Inference metadata confidence 0.99 gives 36.036 per CRITICAL Finding: two missing features sum to 72.072, eight to 288.288, each requiring category cap 40. '
        'Single reciprocal-mapping leakage at confidence 0.88 remains below 40 and receives no new cap annotation.', '',
        '## event_key: pinned contract and adverse practical specificity', '',
        'There are **68 representation cells, comprising 34 logical CSV/pqstr case pairs**. Each gains exactly '
        '§schema.parse_failures::column:event_key§, severity HIGH, full counter population, and one positive check/subject-specific normative opportunity. '
        'Its optional confidence expectation remains unset, consistent with the existing annotation style. '
        'The global absent-check entry for schema.parse_failures is removed in 66 cells. In the two multicategory cells the check was already expected on signal_x; '
        'that expectation is preserved and the event_key subject is added. Other expectations, including exact split Findings and suppression, remain unchanged.', '',
        'Pinned-contract interpretation: C3/C4 require this Finding under the existing date-name heuristic even though the report infers the column as text. '
        'Practical interpretation: the source values are legitimate non-null identifier strings §event_<integer>§, not physically malformed datetime values. '
        '**HIGH datetime parse warnings on valid identifiers remain ADVERSE practical Alpha specificity behavior.** '
        'Normative detection of this heuristic is not a new physical TP and is not a favorable user-facing outcome.', '',
        'A fresh read-only audit verifies all values in these 68 correctness sources, plus eight related sampling sources, as legitimate identifiers. '
        'Every correctness event_key Finding retains HIGH severity, confidence 0.62 and 10,000 attempts/failures. '
        'Its isolated schema penalty is 10.04; keyed-duplicate controls and otherwise quiet group cases consequently start at readiness 90 and report confidence 81. '
        'For example, key excess 0 or 9 has readiness 90, 10 or 11 has 80, and 100 or 101 has 73. '
        'Absolute scores include this unchanged background warning. Within-family transitions describe the existing inputs, not counterfactual nuisance-free scores. '
        'Composites retain other penalties and remediation; no target score is recalculated.', '',
        f'The {artifact("practical-specificity record", "practical_event_key.json")} retains all 68 original Findings, report/source hashes, readiness, '
        'total risk, schema risk and explicit false primary-clean eligibility. '
        f'Readiness across these cells ranges from {min(p["readiness"] for p in practical)} to {max(p["readiness"] for p in practical)}. '
        'This paired inventory gives both affected IDs and original report links.', '',
        '| Logical case | CSV cell / report | pqstr cell / report | Readiness CSV / pqstr |',
        '| --- | --- | --- | --- |',
    ]
    pairs = defaultdict(dict)
    for p in practical:
        pairs[p['logical_case_id']][p['scenario_id'].rsplit('.', 1)[-1]] = p
    for logical, pair in sorted(pairs.items()):
        a, b = pair['csv'], pair['pqstr']
        lines.append(f'| §{logical}§ | {source(a["scenario_id"])}; {report(a)} | {source(b["scenario_id"])}; {report(b)} | {a["readiness"]} / {b["readiness"]} |')
    lines += [
        '',
        'The primary-clean frame remains eight preregistered controls and 226 negative opportunities: FPR 0/226 and 0/8 affected controls. '
        'None of the 68 event_key cells is added post hoc. The eight separate registered specificity challenges retain their original frame: '
        'six expected INFO identifier Findings, physical INFO FPR 6/216 and LOW-or-higher 0/216. '
        'Zero primary-clean or fixed-frame normative FPR does not establish zero practical false alarms on other valid schema shapes.', '',
        '## ORIGINAL PREREGISTERED-LABEL RESULT versus ADJUDICATED PINNED-CONTRACT RESULT', '',
        'Whole-cell conformance uses one standard-context, repeat-0, full-reference correctness report per cell: 320 cells, 160 per representation. '
        'Other repeats, sampling arms, scale measurements and diagnostics do not enlarge this denominator. '
        'The original 86 failures comprise 68 event_key frame disagreements and 18 cap-label defects. '
        'The adjudicated value uses the existing evaluator, including Finding matching, absent behavior, out-of-frame behavior, severity, '
        'original explicit confidence labels, exact hard gates, category caps and suppression.', '',
        '| Metric | ORIGINAL PREREGISTERED-LABEL RESULT | ADJUDICATED PINNED-CONTRACT RESULT |',
        '| --- | --- | --- |',
    ]
    for key, label in (
        ('whole_cell_normative_conformance', 'Whole-cell normative conformance'),
        ('category_caps_correctness', 'Exact category-cap correctness'),
        ('gate_correctness', 'Exact hard-gate set correctness'),
        ('score_respects_gates', 'Readiness respects hard gates'),
        ('suppression_correctness', 'Explicit suppression opportunities'),
        ('normative_scenario_detection', 'Normatively positive scenario detection'),
        ('normative_all_required', 'All required normative Findings in a positive scenario'),
    ):
        lines.append(f'| {label} | {ratio(before[key])} | {ratio(after[key])} |')
    lines.append(f'| Out-of-frame Finding occurrences | {before["out_of_frame_findings"]} | {after["out_of_frame_findings"]} |')
    bi, ai = before['independent_report_field_checks'], after['independent_report_field_checks']
    for label, num, den in (
        ('Independent expected Finding matches', 'matched_expected_findings', 'expected_findings'),
        ('Independent severity matches', 'correct_expected_severity', 'expected_findings'),
        ('Independent original explicit confidence labels', 'correct_explicit_confidence', 'explicit_confidence_labels'),
        ('Independent positive gate occurrences', 'matched_gate_occurrences', 'expected_gate_occurrences'),
        ('Independent suppression', 'correct_suppression', 'suppression_opportunities'),
    ):
        lines.append(f'| {label} | {bi.get(num, 0)}/{bi.get(den, 0)} | {ai.get(num, 0)}/{ai.get(den, 0)} |')
    lines += [
        '',
        'Independent counts use exact check/subject matches and original report severities and gate fields, not stored success labels. '
        f'Unexpected gate occurrences remain {ai.get("unexpected_gate_occurrences", 0)}. '
        'Three disposable software counterexamples confirm that removing the new expected Finding, lowering its severity, or removing a required category cap each fails conformance. '
        'Those copies are never saved as scientific evidence and cause no target calls.', '',
        '| Label set / cutoff | TP | FP | FN | TN | Positive opportunities | Total coverage | Severity correctness |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |',
    ]
    for label, values in (('Original', before), ('Adjudicated', after)):
        for cutoff in ('INFO', 'LOW'):
            m = values['detection'][f'normative/{cutoff}/combined']
            lines.append(f'| {label} / {cutoff} | {m["tp"]} | {m["fp"]} | {m["fn"]} | {m["tn"]} | {m["planned_positive_opportunities"]} | {ratio(m["successful_report_coverage"])} | {ratio(m["severity_correctness"])} |')
    lines += [
        '',
        'The correction adds 68 normative positive opportunities and removes no normative negative opportunities: total coverage denominator moves from 9,106 to 9,174. '
        'Cap corrections change whole-cell conformance without changing opportunities. These are openly adjudicated denominators, never presented as the original preregistered frame. '
        'At INFO, expected-Finding precision/recall become 320/320 and negative-opportunity FPR remains 0/8854. '
        'At LOW, six original INFO expectations are excluded from positive support; all 68 HIGH event_key expectations remain. '
        f'The {artifact("machine-readable summary", "summary.json")} retains both cutoffs and each representation separately.', '',
        '## Preserved physical metrics and unfavorable observations', '',
        'Physical truth, detector mappings, opportunity IDs, strata and primary-clean eligibility are unchanged. '
        'The approved shared-entity OR counts one physical opportunity while check-specific normative expectations and suppression remain separate. '
        'No malformed-datetime physical truth for event_key is invented.', '',
        '| Physical cutoff | TP | FP | FN | TN | Detection / positives | FPR / negatives | Coverage |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |',
    ]
    for cutoff in ('INFO', 'LOW'):
        m = after['detection'][f'controlled_condition/{cutoff}/combined']
        lines.append(f'| {cutoff} | {m["tp"]} | {m["fp"]} | {m["fn"]} | {m["tn"]} | {ratio(m["conditional_recall"])} | {ratio(m["conditional_fpr"])} | {ratio(m["successful_report_coverage"])} |')
    lines += [
        '',
        'Physical detection remains 246/314 and all 68 physical misses remain. These misses are distinct from the coincidentally equal count of 68 event_key warning cells. '
        'Below-threshold defects, collapsed or insufficient support, nonreciprocal leakage, allowlisting and group-split policy/applicability retain their original strata. '
        'Physical positive-scenario detection remains 200/260 and all-required detection 192/260. Complete coverage makes end-to-end physical yield numerically equal conditional recall here; definitions remain separate.', '',
        f'The [original scientific review]({history_base}ALPHA_BENCHMARK_V1_SCIENTIFIC_RESULT_REVIEW.md) remains the detailed immutable record of '
        'every physical miss, all eight sampling disagreements, all 42 format mismatches, determinism pairs, score boundaries and performance observations. '
        'Only its V1 normative-label conclusion is superseded by this overlay. Its adverse evidence and original 234/320 result remain preserved.', '',
        'Sampling retains 36 reference/bounded pairs and 72 diagnostics: 28 exact Finding-set agreements and eight disagreements. '
        'The sample remains the fixed HEAD_STRIDE_V1 geometry; exact repetition does not remove its blind spots.', '',
        '| Existing sampling disagreement | Full-reference to bounded observation, unchanged |',
        '| --- | --- |',
        '| cardinality.head | Distinct share 0.98 to 0.97; LOW warning disappears; readiness 97 to 100 |',
        '| class_boundary.middle | Minority share 0.10 to 0.09; MEDIUM warning appears; readiness 100 to 92 |',
        '| class_boundary.tail | Minority share 0.10 to 0.09; MEDIUM warning appears; readiness 100 to 92 |',
        '| class_rare.gaps | Rare class absent from sample; HIGH warning disappears; readiness 83 to 100 |',
        '| duplicate_keys.gaps | Duplicate destinations outside sample; duplicate warning disappears; event_key persists; readiness 73 to 90 |',
        '| duplicate_rows.gaps | Duplicate destinations outside sample; MEDIUM warning disappears; readiness 90 to 100 |',
        '| group.gaps | Repeated-entity participants disappear; recommendation disappears; event_key persists; readiness 79 to 90 |',
        '| leakage.head | Agreement share 0.999 to 0.9985; CRITICAL leakage and hard gate disappear; readiness 60 to 100 |', '',
        'The leakage 60 to 100 change remains a negative sampling result, not improved underlying data. '
        'Full-scan missingness/parse counters retain invariance across their eight pairs. The class_rare diagnostic counts the smallest observed class, '
        'not the injected class with zero sampled members. Primitive availability and all diagnostics are unchanged.', '',
        'Strict format comparisons retain 37 mismatches among 160 CSV/pqstr pairs and five among five eligible native projections: 42 total. '
        'String-transport mismatches concern empty-token versus typed-null string statistics; native mismatches retain string_stats differences for typed values. '
        'All paired Findings, readiness, total/category risks, confidence, gates/caps, analysis_stats and remediation agree. '
        'The original strict comparison is not replaced by a more favorable normalized metric. This is V3, a publication caveat rather than inconsistent risk decisions.', '',
        'Determinism retains 72 within-context repeat pairs with identical canonical bytes/hashes and 159/159 table comparisons '
        '(132 context comparisons plus 27 scale comparisons), supporting only tested cases/repeats/contexts. '
        'Parser/scoring non-monotonicity remains: numeric corruption 2000/10000 gives readiness 89 and Finding confidence 0.70; '
        '4000/10000 gives readiness 90 and confidence 0.62; 6000/10000 loses numeric dominance and gives readiness 100. '
        'Readiness and confidence are not calibrated or monotonic physical-damage measures. A collapsed class can also escape the diversity-dependent imbalance check. '
        'Remediation gains remain heuristic estimates, not measured causal recovery.', '',
        'Performance retains 13 regular-scale cells with three measurements each, the 5M cell with two measurements, and 13 excluded warmups. '
        '5M times remain 914.052132966 and 910.409173628 seconds, median 912.230653297; n=2 is weak descriptive evidence only. '
        'The 1M width-100 native median remains 1148.830717559 seconds. Fixed sampled P does not eliminate full-scan/input costs or make modes equal work. '
        'All 578 monitors remain complete; requested RSS interval is 0.01 seconds and the maximum observed gap is 0.105340397 seconds. '
        'RSS is a sampled worker-tree sum excluding the supervisor, includes worker baseline memory, and can miss brief peaks. '
        'One prepared WSL2/ext4 environment is not a native-Linux replication, cold-cache experiment, production bound or general hardware comparison.', '',
        '## Evidence preservation and validation', '',
        f'The {artifact("preservation record", "evidence_preservation.json")} retains all 1,062 original candidate file hashes before and after processing; inventories match. '
        'Fresh read-only verification matches 370 original source files, 578 ledger reports and 72 original diagnostics to the candidate. '
        'All 15 original evidence-derived tables are regenerated in memory using existing query code and match their CSV bytes. '
        'Original figures, report, receipts, RunSpecs, scenario/expectation snapshots, diagnostics, attempts and instrumentation remain intact.', '',
        '| Integrity binding | Unchanged SHA-256 |', '| --- | --- |',
        f'| Candidate checksum manifest | §{provenance["original_candidate_checksums_sha256"]}§ |',
        f'| Report-hash inventory | §{preservation["report_hash_inventory_sha256"]}§ |',
        f'| Source-hash inventory | §{preservation["source_hash_inventory_sha256"]}§ |',
        f'| Attempt ledger | §{preservation["attempts_sha256"]}§ |',
        f'| Instrumentation | §{preservation["instrumentation_sha256"]}§ |',
        f'| Original scientific review | §{provenance["original_scientific_review_sha256"]}§ |', '',
        'Checks cover typed annotations/opportunities, design-only derivation, independent Finding/severity/gate/suppression evaluation, '
        'three negative software controls, unchanged physical frames/metrics at both cutoffs and representations, source/report/diagnostic/ledger hashes, '
        'byte-identical sampling/determinism/performance/clean tables, deterministic supplemental serialization and the repository public-safety scanner. '
        'An explicit import guard forbids target imports. No target code, primary RunSpec, diagnostic TADR call or scientific worker was executed. No scientific fixture was regenerated.', '',
        'Only ignored review/adjudication artifacts were written. Benchmark tracked files and tadr-core are unchanged; no commit was created. '
        'Campaign status, public RESULTS.md and the candidate are unchanged. No figures or frozen results were generated.', '',
        '## Remaining validity findings and freeze eligibility', '',
        '| ID | Status / severity | Disposition |', '| --- | --- | --- |',
        '| V1 | Resolved by approved adjudication | C1/C2 justify 18 missing caps; C3/C4 justify 68 event_key frames from the pre-execution contract. Original labels and 234/320 are retained; corrected conformance is recomputed from immutable evidence. |',
        '| V2 | IMPORTANT | Valid event_key identifiers trigger HIGH datetime advice and lower absolute readiness in keyed/group and related families. Retain as adverse specificity; qualify primary-clean FPR and scores. No physical or clean denominator change. |',
        '| V3 | IMPORTANT | Retain 42 strict format mismatches and profile-statistic causes while stating that decision fields agree. Do not substitute a post hoc normalized comparison. |',
        '| V4 | MINOR | Permanent docs still include design-time PLANNED/deferred wording; READY source manifest is a launch declaration. Distinguish that history from the completed private candidate before public release. Public status/RESULTS changes are outside this pass. |', '',
        'V2/V3 remain publication caveats and V4 a documentation task. Poor physical detection, nuisance warnings, sampling blind spots and slow runtime do not themselves invalidate the benchmark. '
        'Corrected labels have a pre-execution contract basis; physical truth and scientific inputs did not change; authoritative evidence was not rewritten; '
        'no new integrity issue was found. The remaining critical-condition inventory is explicit in the machine-readable summary.', '',
        f'**Remaining: CRITICAL {counts["CRITICAL"]}; IMPORTANT {counts["IMPORTANT"]}; MINOR {counts["MINOR"]}.**', '',
        f'**{results["verdict"]}**', '',
        'The original candidate must be accompanied by this adjudication record and explicit original-versus-adjudicated labels at any later freeze review. '
        'This pass performs no freeze, publication, commit or scientific rerun.', '',
    ]
    assert len(cap_rows) == 18 and len(event_rows) == 68 and len(pairs) == 34
    return '\n'.join(lines).replace('§', chr(96))
