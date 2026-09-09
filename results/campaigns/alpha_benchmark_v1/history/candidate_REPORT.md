CANDIDATE FOR REVIEW — NOT FROZEN OR PUBLISHED. Execution is complete. Scientific execution revision: a76bb9458b181500c7bfb9efefcfecfbb019b5a9. Post-execution validation and aggregation revision: 4887bd579d394de523bab0ccb227840d66447fd9. See processing_provenance.json for the separately bound processing record. The resolved READY source manifest is retained unchanged; its NOT YET RUN notes describe the launch declaration. References to frozen artifacts in the generated draft describe the proposed final package, pending explicit approval. Execution used Ubuntu 24.04 under WSL2, Linux x86_64, Python 3.11.9, four Polars threads and native ext4 storage. Guest topology and shared host scheduling limit performance generalization. No population estimates or new confidence intervals are inferred.

# ALPHA_BENCHMARK_V1

Target: `tadr-core` `0.1.0`. Algorithm `1.0`, profile `MVP_V1`, bundle `1.0`, baseline `1.0.12`.

Target source distribution: `proprietary`. Run data SHA-256: `09594169259698a4d18bb5ac845e9a572ebb9acba8e82d839dc0ba3a7a25ac50`.

The evaluated TADR Core implementation is proprietary; an external party cannot rebuild the evaluated implementation from public source. Benchmark methodology, synthetic datasets, ground truth, scenario definitions, execution protocol, evaluation and published result artifacts are public. The exact target is identified by versioned metadata and the execution artifact SHA-256. This repository distributes neither the proprietary artifact nor its source code. Re-execution requires authorized artifact access.

Installation artifact SHA-256: `a37ec8d336d16dbe4b7a7448071808daaf5e3e0ab03afe3bb7de0ce6882bc31d`.

Benchmark `0.1.0` at `a76bb9458b181500c7bfb9efefcfecfbb019b5a9`. Environment and dependency identities are retained in environment.json.

## Methodology and scenario matrix

The frozen manifest, scenario snapshots and execution plan define the complete experiment. Ground truth precedes target execution. See the [frozen protocol](protocol.md) and [scenario matrix](tables/scenario_matrix.csv).

## Detection, negative controls and boundary behavior

See [summary table](tables/summary.csv) for matched/missed expectations, absent violations and unexpected Findings. Raw records retain each outcome; counts across repetitions are not independent samples or calibrated precision estimates.

[Per-check metrics](tables/detection_by_check.csv) keep normative conformance and controlled-condition sensitivity separate, with fixed support counts and undefined rates left empty. Finding TP/FP/FN/TN and conditional precision/recall/FPR require a successful canonical report. A target failure without a report is UNEVALUABLE, never a negative prediction or Finding-level FN. Each conditional rate is accompanied by planned/evaluable/unevaluable opportunity counts, positive/negative successful-report coverage and terminal failures by category. End-to-end detection yield is detected positive physical opportunities divided by all planned positive physical opportunities, including those without reports; it is a separate system-level descriptive metric, not recall. [Clean controls](tables/clean_false_positives.csv) separate primary controls from specificity challenges; [boundaries](tables/threshold_boundaries.csv) retain exact construction numerators and denominators. Only the standard-context measured repeat zero enters these scientific queries; formats remain separate.

## Score behavior, hard gates and suppression

The table retains score ranges. Each raw record retains risks, ordered Findings, gates and remediations. Suppressed Findings cannot be reconstructed from final reports.

See [score sweeps](tables/score_sweeps.csv), [composite interactions](tables/composite_interactions.csv) and [ordered remediation](tables/remediation.csv). These are observations, not a scoring oracle.

## Determinism, runtime, throughput and peak RSS

| Scenario / variant | Runs | Runtime median (s) | MAD (s) | Peak RSS median (bytes) | Deterministic |
| --- | ---: | ---: | ---: | ---: | --- |
| challenge.lexical_paid.n10000.csv / full_reference / standard | 1 | 2.05224 | 0 | 1.73474e+08 | True |
| challenge.lexical_paid.n10000.pqstr / full_reference / standard | 1 | 2.07409 | 0 | 1.635e+08 | True |
| class.binary.min0.n10000.csv / full_reference / standard | 1 | 2.36148 | 0 | 1.77353e+08 | True |
| class.binary.min0.n10000.pqstr / full_reference / standard | 1 | 2.61506 | 0 | 1.53522e+08 | True |
| class.binary.min1.n10000.csv / full_reference / standard | 1 | 2.12439 | 0 | 1.70779e+08 | True |
| class.binary.min1.n10000.pqstr / full_reference / standard | 1 | 2.41762 | 0 | 1.55251e+08 | True |
| class.binary.min100.n10000.csv / full_reference / standard | 1 | 2.07272 | 0 | 1.74961e+08 | True |
| class.binary.min100.n10000.pqstr / full_reference / standard | 1 | 2.421 | 0 | 1.51499e+08 | True |
| class.binary.min1000.n10000.csv / full_reference / standard | 1 | 2.18398 | 0 | 1.70103e+08 | True |
| class.binary.min1000.n10000.pqstr / full_reference / standard | 1 | 2.43679 | 0 | 1.55378e+08 | True |
| class.binary.min1001.n10000.csv / full_reference / standard | 1 | 2.15114 | 0 | 1.73359e+08 | True |
| class.binary.min1001.n10000.pqstr / full_reference / standard | 1 | 2.39526 | 0 | 1.57512e+08 | True |
| class.binary.min199.n10000.csv / full_reference / standard | 1 | 2.12213 | 0 | 1.75165e+08 | True |
| class.binary.min199.n10000.pqstr / full_reference / standard | 1 | 2.39768 | 0 | 1.51421e+08 | True |
| class.binary.min200.n10000.csv / full_reference / standard | 1 | 2.2087 | 0 | 1.75342e+08 | True |
| class.binary.min200.n10000.pqstr / full_reference / standard | 1 | 2.45304 | 0 | 1.55496e+08 | True |
| class.binary.min201.n10000.csv / full_reference / standard | 1 | 2.1857 | 0 | 1.7152e+08 | True |
| class.binary.min201.n10000.pqstr / full_reference / standard | 1 | 2.46234 | 0 | 1.53113e+08 | True |
| class.binary.min5000.n10000.csv / full_reference / standard | 1 | 2.23198 | 0 | 1.75325e+08 | True |
| class.binary.min5000.n10000.pqstr / full_reference / standard | 1 | 2.50622 | 0 | 1.54862e+08 | True |
| class.binary.min999.n10000.csv / full_reference / standard | 1 | 2.16452 | 0 | 1.71516e+08 | True |
| class.binary.min999.n10000.pqstr / full_reference / standard | 1 | 2.44376 | 0 | 1.53338e+08 | True |
| class.support.n100.min5.csv / full_reference / standard | 1 | 0.219731 | 0 | 1.51532e+08 | True |
| class.support.n100.min5.pqstr / full_reference / standard | 1 | 0.250509 | 0 | 1.34762e+08 | True |
| class.support.n99.min5.csv / full_reference / standard | 1 | 0.225563 | 0 | 1.55836e+08 | True |
| class.support.n99.min5.pqstr / full_reference / standard | 1 | 0.224626 | 0 | 1.40603e+08 | True |
| clean.analytics.n10000.csv / full_reference / standard | 1 | 1.65695 | 0 | 1.72433e+08 | True |
| clean.analytics.n10000.pqstr / full_reference / standard | 1 | 1.82421 | 0 | 1.5836e+08 | True |
| clean.classification.n10000.csv / full_reference / decimal_high | 2 | 2.11504 | 0.0580966 | 1.74682e+08 | True |
| clean.classification.n10000.csv / full_reference / decimal_low | 2 | 2.06365 | 0.00701513 | 1.73752e+08 | True |
| clean.classification.n10000.csv / full_reference / hash_fortytwo | 2 | 2.09041 | 0.0065638 | 1.76355e+08 | True |
| clean.classification.n10000.csv / full_reference / hash_one | 2 | 2.11516 | 0.0366947 | 1.74105e+08 | True |
| clean.classification.n10000.csv / full_reference / standard | 2 | 2.08147 | 0.0172482 | 1.72698e+08 | True |
| clean.classification.n10000.csv / full_reference / timezone_berlin | 2 | 2.07868 | 0.0109246 | 1.73382e+08 | True |
| clean.classification.n10000.pqstr / full_reference / standard | 1 | 2.46729 | 0 | 1.56254e+08 | True |
| clean.regression.n10000.csv / full_reference / standard | 1 | 2.51459 | 0 | 1.77279e+08 | True |
| clean.regression.n10000.pqstr / full_reference / standard | 1 | 2.76313 | 0 | 1.52199e+08 | True |
| clean.time_series.n10000.csv / full_reference / standard | 1 | 2.62409 | 0 | 1.68182e+08 | True |
| clean.time_series.n10000.pqstr / full_reference / decimal_high | 2 | 2.8263 | 0.0211606 | 1.60369e+08 | True |
| clean.time_series.n10000.pqstr / full_reference / decimal_low | 2 | 2.7991 | 0.00767148 | 1.61954e+08 | True |
| clean.time_series.n10000.pqstr / full_reference / hash_fortytwo | 2 | 2.77223 | 0.0285502 | 1.59037e+08 | True |
| clean.time_series.n10000.pqstr / full_reference / hash_one | 2 | 2.76508 | 0.00511248 | 1.60729e+08 | True |
| clean.time_series.n10000.pqstr / full_reference / standard | 2 | 2.76648 | 0.00346243 | 1.60799e+08 | True |
| clean.time_series.n10000.pqstr / full_reference / timezone_berlin | 2 | 2.74726 | 0.0463824 | 1.60502e+08 | True |
| composite.duplicates_group_group.n10000.csv / full_reference / standard | 1 | 3.03079 | 0 | 1.75542e+08 | True |
| composite.duplicates_group_group.n10000.pqstr / full_reference / standard | 1 | 3.36963 | 0 | 1.64667e+08 | True |
| composite.duplicates_group_random.n10000.csv / full_reference / standard | 1 | 3.06785 | 0 | 1.8314e+08 | True |
| composite.duplicates_group_random.n10000.pqstr / full_reference / standard | 1 | 3.35531 | 0 | 1.67268e+08 | True |
| composite.inference_missing.n10000.csv / full_reference / standard | 1 | 1.6381 | 0 | 1.70836e+08 | True |
| composite.inference_missing.n10000.pqstr / full_reference / standard | 1 | 1.88558 | 0 | 1.52203e+08 | True |
| composite.leak_inference.n10000.csv / full_reference / standard | 1 | 2.87036 | 0 | 1.76726e+08 | True |
| composite.leak_inference.n10000.pqstr / full_reference / standard | 1 | 3.16343 | 0 | 1.54554e+08 | True |
| composite.leak_missing.n10000.csv / full_reference / standard | 1 | 2.79746 | 0 | 1.78663e+08 | True |
| composite.leak_missing.n10000.pqstr / full_reference / standard | 1 | 3.0764 | 0 | 1.53633e+08 | True |
| composite.missing_parse.n10000.csv / full_reference / standard | 1 | 1.58273 | 0 | 1.75333e+08 | True |
| composite.missing_parse.n10000.pqstr / full_reference / standard | 1 | 1.79618 | 0 | 1.55501e+08 | True |
| composite.multicategory.n10000.csv / full_reference / standard | 1 | 3.0747 | 0 | 1.7646e+08 | True |
| composite.multicategory.n10000.pqstr / full_reference / standard | 1 | 3.30711 | 0 | 1.65966e+08 | True |
| composite.quality_accumulation_k1.n10000.csv / full_reference / standard | 1 | 2.39857 | 0 | 1.80269e+08 | True |
| composite.quality_accumulation_k1.n10000.pqstr / full_reference / standard | 1 | 2.60122 | 0 | 1.7084e+08 | True |
| composite.quality_accumulation_k2.n10000.csv / full_reference / standard | 1 | 2.32754 | 0 | 1.78229e+08 | True |
| composite.quality_accumulation_k2.n10000.pqstr / full_reference / standard | 1 | 2.60517 | 0 | 1.71147e+08 | True |
| composite.quality_accumulation_k3.n10000.csv / full_reference / standard | 1 | 2.31429 | 0 | 1.86044e+08 | True |
| composite.quality_accumulation_k3.n10000.pqstr / full_reference / standard | 1 | 2.42893 | 0 | 1.67707e+08 | True |
| composite.timestamp_null_random.n10000.csv / full_reference / standard | 1 | 2.64678 | 0 | 1.78999e+08 | True |
| composite.timestamp_null_random.n10000.pqstr / full_reference / standard | 1 | 2.85811 | 0 | 1.64151e+08 | True |
| composite.timestamp_random.n10000.csv / full_reference / decimal_high | 2 | 2.45038 | 0.0758372 | 1.76779e+08 | True |
| composite.timestamp_random.n10000.csv / full_reference / decimal_low | 2 | 2.45339 | 0.0878888 | 1.74311e+08 | True |
| composite.timestamp_random.n10000.csv / full_reference / hash_fortytwo | 2 | 2.5239 | 0.00132731 | 1.78756e+08 | True |
| composite.timestamp_random.n10000.csv / full_reference / hash_one | 2 | 2.46502 | 0.00357216 | 1.73144e+08 | True |
| composite.timestamp_random.n10000.csv / full_reference / standard | 2 | 2.53906 | 0.00488565 | 1.7621e+08 | True |
| composite.timestamp_random.n10000.csv / full_reference / timezone_berlin | 2 | 2.51985 | 0.0106618 | 1.78172e+08 | True |
| composite.timestamp_random.n10000.pqstr / full_reference / standard | 1 | 2.91886 | 0 | 1.6146e+08 | True |
| duplicate.keys.e0.n10000.csv / full_reference / standard | 1 | 2.16698 | 0 | 1.8305e+08 | True |
| duplicate.keys.e0.n10000.pqstr / full_reference / standard | 1 | 2.45543 | 0 | 1.61604e+08 | True |
| duplicate.keys.e10.n10000.csv / full_reference / standard | 1 | 2.22708 | 0 | 1.75735e+08 | True |
| duplicate.keys.e10.n10000.pqstr / full_reference / standard | 1 | 2.46637 | 0 | 1.61874e+08 | True |
| duplicate.keys.e100.n10000.csv / full_reference / standard | 1 | 2.19004 | 0 | 1.8183e+08 | True |
| duplicate.keys.e100.n10000.pqstr / full_reference / decimal_high | 2 | 2.30249 | 0.0107859 | 1.65347e+08 | True |
| duplicate.keys.e100.n10000.pqstr / full_reference / decimal_low | 2 | 2.2557 | 0.0904124 | 1.622e+08 | True |
| duplicate.keys.e100.n10000.pqstr / full_reference / hash_fortytwo | 2 | 2.39227 | 0.0156673 | 1.64323e+08 | True |
| duplicate.keys.e100.n10000.pqstr / full_reference / hash_one | 2 | 2.38382 | 0.0105847 | 1.60905e+08 | True |
| duplicate.keys.e100.n10000.pqstr / full_reference / standard | 2 | 2.32002 | 0.0229042 | 1.62306e+08 | True |
| duplicate.keys.e100.n10000.pqstr / full_reference / timezone_berlin | 2 | 2.26905 | 0.119258 | 1.62845e+08 | True |
| duplicate.keys.e101.n10000.csv / full_reference / standard | 1 | 2.38266 | 0 | 1.81318e+08 | True |
| duplicate.keys.e101.n10000.pqstr / full_reference / standard | 1 | 2.65707 | 0 | 1.64639e+08 | True |
| duplicate.keys.e11.n10000.csv / full_reference / standard | 1 | 2.30996 | 0 | 1.7469e+08 | True |
| duplicate.keys.e11.n10000.pqstr / full_reference / standard | 1 | 2.50186 | 0 | 1.62292e+08 | True |
| duplicate.keys.e9.n10000.csv / full_reference / standard | 1 | 2.25721 | 0 | 1.79462e+08 | True |
| duplicate.keys.e9.n10000.pqstr / full_reference / standard | 1 | 2.44243 | 0 | 1.62124e+08 | True |
| duplicate.keys.e99.n10000.csv / full_reference / standard | 1 | 2.20909 | 0 | 1.83632e+08 | True |
| duplicate.keys.e99.n10000.pqstr / full_reference / standard | 1 | 2.45289 | 0 | 1.64069e+08 | True |
| duplicate.rows.e0.n10000.csv / full_reference / standard | 1 | 1.70894 | 0 | 1.75079e+08 | True |
| duplicate.rows.e0.n10000.pqstr / full_reference / standard | 1 | 1.8446 | 0 | 1.5727e+08 | True |
| duplicate.rows.e10.n10000.csv / full_reference / standard | 1 | 1.70945 | 0 | 1.70639e+08 | True |
| duplicate.rows.e10.n10000.pqstr / full_reference / standard | 1 | 1.87656 | 0 | 1.59404e+08 | True |
| duplicate.rows.e100.n10000.csv / full_reference / standard | 1 | 1.69764 | 0 | 1.67617e+08 | True |
| duplicate.rows.e100.n10000.pqstr / full_reference / standard | 1 | 1.8519 | 0 | 1.5992e+08 | True |
| duplicate.rows.e1000.n10000.csv / full_reference / standard | 1 | 1.6545 | 0 | 1.71491e+08 | True |
| duplicate.rows.e1000.n10000.pqstr / full_reference / standard | 1 | 1.79333 | 0 | 1.57561e+08 | True |
| duplicate.rows.e101.n10000.csv / full_reference / standard | 1 | 1.66084 | 0 | 1.66826e+08 | True |
| duplicate.rows.e101.n10000.pqstr / full_reference / standard | 1 | 1.8186 | 0 | 1.59416e+08 | True |
| duplicate.rows.e11.n10000.csv / full_reference / standard | 1 | 1.65043 | 0 | 1.74944e+08 | True |
| duplicate.rows.e11.n10000.pqstr / full_reference / standard | 1 | 1.81704 | 0 | 1.599e+08 | True |
| duplicate.rows.e499.n10000.csv / full_reference / standard | 1 | 1.61582 | 0 | 1.78881e+08 | True |
| duplicate.rows.e499.n10000.pqstr / full_reference / standard | 1 | 1.83741 | 0 | 1.59769e+08 | True |
| duplicate.rows.e500.n10000.csv / full_reference / decimal_high | 2 | 1.60834 | 0.0375371 | 1.75073e+08 | True |
| duplicate.rows.e500.n10000.csv / full_reference / decimal_low | 2 | 1.51114 | 0.0307309 | 1.76347e+08 | True |
| duplicate.rows.e500.n10000.csv / full_reference / hash_fortytwo | 2 | 1.6287 | 0.00286995 | 1.73492e+08 | True |
| duplicate.rows.e500.n10000.csv / full_reference / hash_one | 2 | 1.58995 | 0.018608 | 1.67283e+08 | True |
| duplicate.rows.e500.n10000.csv / full_reference / standard | 2 | 1.59463 | 0.00307984 | 1.74154e+08 | True |
| duplicate.rows.e500.n10000.csv / full_reference / timezone_berlin | 2 | 1.50743 | 0.00423936 | 1.75131e+08 | True |
| duplicate.rows.e500.n10000.pqstr / full_reference / standard | 1 | 1.83716 | 0 | 1.62304e+08 | True |
| duplicate.rows.e501.n10000.csv / full_reference / standard | 1 | 1.64777 | 0 | 1.75129e+08 | True |
| duplicate.rows.e501.n10000.pqstr / full_reference / standard | 1 | 1.82934 | 0 | 1.57938e+08 | True |
| duplicate.rows.e9.n10000.csv / full_reference / standard | 1 | 1.63538 | 0 | 1.72954e+08 | True |
| duplicate.rows.e9.n10000.pqstr / full_reference / standard | 1 | 1.83272 | 0 | 1.58962e+08 | True |
| duplicate.rows.e99.n10000.csv / full_reference / standard | 1 | 1.64489 | 0 | 1.72962e+08 | True |
| duplicate.rows.e99.n10000.pqstr / full_reference / standard | 1 | 1.86576 | 0 | 1.60145e+08 | True |
| group.group.r0.n10000.csv / full_reference / standard | 1 | 3.04533 | 0 | 1.76865e+08 | True |
| group.group.r0.n10000.pqstr / full_reference / standard | 1 | 3.29749 | 0 | 1.62779e+08 | True |
| group.group.r1999.n10000.csv / full_reference / standard | 1 | 3.05876 | 0 | 1.80277e+08 | True |
| group.group.r1999.n10000.pqstr / full_reference / standard | 1 | 3.31038 | 0 | 1.64786e+08 | True |
| group.group.r2000.n10000.csv / full_reference / standard | 1 | 2.98412 | 0 | 1.77697e+08 | True |
| group.group.r2000.n10000.pqstr / full_reference / standard | 1 | 3.29828 | 0 | 1.66908e+08 | True |
| group.group.r2001.n10000.csv / full_reference / standard | 1 | 3.0635 | 0 | 1.80883e+08 | True |
| group.group.r2001.n10000.pqstr / full_reference / standard | 1 | 3.3118 | 0 | 1.67031e+08 | True |
| group.group.r499.n10000.csv / full_reference / standard | 1 | 3.03946 | 0 | 1.75174e+08 | True |
| group.group.r499.n10000.pqstr / full_reference / standard | 1 | 3.34977 | 0 | 1.64844e+08 | True |
| group.group.r500.n10000.csv / full_reference / standard | 1 | 3.05126 | 0 | 1.77926e+08 | True |
| group.group.r500.n10000.pqstr / full_reference / standard | 1 | 3.34606 | 0 | 1.64213e+08 | True |
| group.group.r501.n10000.csv / full_reference / standard | 1 | 3.07732 | 0 | 1.77959e+08 | True |
| group.group.r501.n10000.pqstr / full_reference / standard | 1 | 3.30747 | 0 | 1.61497e+08 | True |
| group.random.r0.n10000.csv / full_reference / standard | 1 | 3.03898 | 0 | 1.81559e+08 | True |
| group.random.r0.n10000.pqstr / full_reference / standard | 1 | 3.33876 | 0 | 1.60309e+08 | True |
| group.random.r1999.n10000.csv / full_reference / standard | 1 | 3.04718 | 0 | 1.81379e+08 | True |
| group.random.r1999.n10000.pqstr / full_reference / standard | 1 | 3.3624 | 0 | 1.66527e+08 | True |
| group.random.r2000.n10000.csv / full_reference / decimal_high | 2 | 3.01518 | 0.121572 | 1.82934e+08 | True |
| group.random.r2000.n10000.csv / full_reference / decimal_low | 2 | 2.90378 | 0.0142268 | 1.77506e+08 | True |
| group.random.r2000.n10000.csv / full_reference / hash_fortytwo | 2 | 2.92957 | 0.0125722 | 1.81404e+08 | True |
| group.random.r2000.n10000.csv / full_reference / hash_one | 2 | 2.96091 | 0.0409467 | 1.79458e+08 | True |
| group.random.r2000.n10000.csv / full_reference / standard | 2 | 2.97672 | 0.00946557 | 1.79468e+08 | True |
| group.random.r2000.n10000.csv / full_reference / timezone_berlin | 2 | 2.82336 | 0.0891788 | 1.81256e+08 | True |
| group.random.r2000.n10000.pqstr / full_reference / standard | 1 | 3.35997 | 0 | 1.64966e+08 | True |
| group.random.r2001.n10000.csv / full_reference / standard | 1 | 3.04919 | 0 | 1.76046e+08 | True |
| group.random.r2001.n10000.pqstr / full_reference / standard | 1 | 3.32968 | 0 | 1.67862e+08 | True |
| group.random.r499.n10000.csv / full_reference / standard | 1 | 3.04502 | 0 | 1.7859e+08 | True |
| group.random.r499.n10000.pqstr / full_reference / standard | 1 | 3.33387 | 0 | 1.64151e+08 | True |
| group.random.r500.n10000.csv / full_reference / standard | 1 | 3.0247 | 0 | 1.82424e+08 | True |
| group.random.r500.n10000.pqstr / full_reference / standard | 1 | 3.32999 | 0 | 1.62669e+08 | True |
| group.random.r501.n10000.csv / full_reference / standard | 1 | 3.02937 | 0 | 1.8373e+08 | True |
| group.random.r501.n10000.pqstr / full_reference / standard | 1 | 3.30141 | 0 | 1.60117e+08 | True |
| group.time.r0.n10000.csv / full_reference / standard | 1 | 3.13976 | 0 | 1.74199e+08 | True |
| group.time.r0.n10000.pqstr / full_reference / standard | 1 | 3.34794 | 0 | 1.63951e+08 | True |
| group.time.r1999.n10000.csv / full_reference / standard | 1 | 3.01179 | 0 | 1.82616e+08 | True |
| group.time.r1999.n10000.pqstr / full_reference / standard | 1 | 3.39654 | 0 | 1.63455e+08 | True |
| group.time.r2000.n10000.csv / full_reference / standard | 1 | 3.07797 | 0 | 1.77463e+08 | True |
| group.time.r2000.n10000.pqstr / full_reference / standard | 1 | 3.23999 | 0 | 1.67133e+08 | True |
| group.time.r2001.n10000.csv / full_reference / standard | 1 | 2.97171 | 0 | 1.81326e+08 | True |
| group.time.r2001.n10000.pqstr / full_reference / standard | 1 | 3.28636 | 0 | 1.65036e+08 | True |
| group.time.r499.n10000.csv / full_reference / standard | 1 | 3.00832 | 0 | 1.76665e+08 | True |
| group.time.r499.n10000.pqstr / full_reference / standard | 1 | 3.26404 | 0 | 1.60473e+08 | True |
| group.time.r500.n10000.csv / full_reference / standard | 1 | 2.97362 | 0 | 1.78221e+08 | True |
| group.time.r500.n10000.pqstr / full_reference / standard | 1 | 3.27372 | 0 | 1.61874e+08 | True |
| group.time.r501.n10000.csv / full_reference / standard | 1 | 3.04619 | 0 | 1.80748e+08 | True |
| group.time.r501.n10000.pqstr / full_reference / standard | 1 | 3.32741 | 0 | 1.62111e+08 | True |
| identifier.measurement.u9799.n10000.csv / full_reference / standard | 1 | 1.9633 | 0 | 1.7519e+08 | True |
| identifier.measurement.u9799.n10000.pqstr / full_reference / standard | 1 | 2.16973 | 0 | 1.6103e+08 | True |
| identifier.measurement.u9800.n10000.csv / full_reference / standard | 1 | 1.93002 | 0 | 1.77869e+08 | True |
| identifier.measurement.u9800.n10000.pqstr / full_reference / standard | 1 | 2.14364 | 0 | 1.63844e+08 | True |
| identifier.measurement.u9801.n10000.csv / full_reference / standard | 1 | 2.04037 | 0 | 1.79692e+08 | True |
| identifier.measurement.u9801.n10000.pqstr / full_reference / standard | 1 | 2.1756 | 0 | 1.59928e+08 | True |
| identifier.probe_id.u9799.n10000.csv / full_reference / standard | 1 | 1.8876 | 0 | 1.77054e+08 | True |
| identifier.probe_id.u9799.n10000.pqstr / full_reference / standard | 1 | 2.09932 | 0 | 1.63049e+08 | True |
| identifier.probe_id.u9800.n10000.csv / full_reference / standard | 1 | 1.89711 | 0 | 1.76955e+08 | True |
| identifier.probe_id.u9800.n10000.pqstr / full_reference / standard | 1 | 2.05865 | 0 | 1.6382e+08 | True |
| identifier.probe_id.u9801.n10000.csv / full_reference / standard | 1 | 1.86643 | 0 | 1.76722e+08 | True |
| identifier.probe_id.u9801.n10000.pqstr / full_reference / standard | 1 | 2.06059 | 0 | 1.59785e+08 | True |
| identifier.support.n100.csv / full_reference / standard | 1 | 0.217859 | 0 | 1.49971e+08 | True |
| identifier.support.n100.pqstr / full_reference / standard | 1 | 0.22039 | 0 | 1.36434e+08 | True |
| identifier.support.n99.csv / full_reference / standard | 1 | 0.220439 | 0 | 1.55648e+08 | True |
| identifier.support.n99.pqstr / full_reference / standard | 1 | 0.211895 | 0 | 1.33812e+08 | True |
| inference.analytics.complete.n10000.csv / full_reference / standard | 1 | 1.63267 | 0 | 1.74678e+08 | True |
| inference.analytics.complete.n10000.pqstr / full_reference / standard | 1 | 1.82925 | 0 | 1.58441e+08 | True |
| inference.analytics.empty.n10000.csv / full_reference / standard | 1 | 1.63297 | 0 | 1.7494e+08 | True |
| inference.analytics.empty.n10000.pqstr / full_reference / standard | 1 | 1.79192 | 0 | 1.55668e+08 | True |
| inference.analytics.null.n10000.csv / full_reference / standard | 1 | 1.61905 | 0 | 1.70471e+08 | True |
| inference.analytics.null.n10000.pqstr / full_reference / standard | 1 | 1.80547 | 0 | 1.56201e+08 | True |
| inference.analytics.omit_one.n10000.csv / full_reference / standard | 1 | 1.62282 | 0 | 1.71528e+08 | True |
| inference.analytics.omit_one.n10000.pqstr / full_reference / decimal_high | 2 | 1.84273 | 0.00263862 | 1.5931e+08 | True |
| inference.analytics.omit_one.n10000.pqstr / full_reference / decimal_low | 2 | 1.76528 | 0.0469987 | 1.58898e+08 | True |
| inference.analytics.omit_one.n10000.pqstr / full_reference / hash_fortytwo | 2 | 1.79919 | 0.0318609 | 1.58804e+08 | True |
| inference.analytics.omit_one.n10000.pqstr / full_reference / hash_one | 2 | 1.6789 | 0.010233 | 1.58876e+08 | True |
| inference.analytics.omit_one.n10000.pqstr / full_reference / standard | 2 | 1.79789 | 5.8554e-05 | 1.60842e+08 | True |
| inference.analytics.omit_one.n10000.pqstr / full_reference / timezone_berlin | 2 | 1.75301 | 0.0209659 | 1.6297e+08 | True |
| inference.analytics.omit_two.n10000.csv / full_reference / standard | 1 | 1.62061 | 0 | 1.75186e+08 | True |
| inference.analytics.omit_two.n10000.pqstr / full_reference / standard | 1 | 1.78678 | 0 | 1.56324e+08 | True |
| inference.analytics.roles_only_excluded.n10000.csv / full_reference / standard | 1 | 2.20272 | 0 | 1.77046e+08 | True |
| inference.analytics.roles_only_excluded.n10000.pqstr / full_reference / standard | 1 | 2.43739 | 0 | 1.60891e+08 | True |
| inference.analytics.superset.n10000.csv / full_reference / standard | 1 | 1.61268 | 0 | 1.69644e+08 | True |
| inference.analytics.superset.n10000.pqstr / full_reference / standard | 1 | 1.81081 | 0 | 1.58343e+08 | True |
| inference.classification.omit_one.n10000.csv / full_reference / standard | 1 | 2.18463 | 0 | 1.75043e+08 | True |
| inference.classification.omit_one.n10000.pqstr / full_reference / standard | 1 | 2.47117 | 0 | 1.55951e+08 | True |
| inference.regression.omit_one.n10000.csv / full_reference / standard | 1 | 2.54589 | 0 | 1.77574e+08 | True |
| inference.regression.omit_one.n10000.pqstr / full_reference / standard | 1 | 2.72042 | 0 | 1.5759e+08 | True |
| inference.time_series.omit_one.n10000.csv / full_reference / standard | 1 | 2.59422 | 0 | 1.70373e+08 | True |
| inference.time_series.omit_one.n10000.pqstr / full_reference / standard | 1 | 2.90798 | 0 | 1.61845e+08 | True |
| leak.control.allowlisted_copy.n10000.csv / full_reference / standard | 1 | 2.70905 | 0 | 1.72417e+08 | True |
| leak.control.allowlisted_copy.n10000.pqstr / full_reference / standard | 1 | 2.99652 | 0 | 1.54608e+08 | True |
| leak.control.bool_numeric_mapping.n10000.csv / full_reference / standard | 1 | 2.62198 | 0 | 1.67772e+08 | True |
| leak.control.bool_numeric_mapping.n10000.pqstr / full_reference / standard | 1 | 2.88726 | 0 | 1.55554e+08 | True |
| leak.control.constant_target.n10000.csv / full_reference / standard | 1 | 2.99444 | 0 | 1.78688e+08 | True |
| leak.control.constant_target.n10000.pqstr / full_reference / standard | 1 | 3.24013 | 0 | 1.53555e+08 | True |
| leak.control.joint_mode_exceptions.n10000.csv / full_reference / standard | 1 | 2.5201 | 0 | 1.76202e+08 | True |
| leak.control.joint_mode_exceptions.n10000.pqstr / full_reference / standard | 1 | 2.79586 | 0 | 1.54915e+08 | True |
| leak.control.many_to_one.n10000.csv / full_reference / standard | 1 | 2.52148 | 0 | 1.7322e+08 | True |
| leak.control.many_to_one.n10000.pqstr / full_reference / standard | 1 | 2.84833 | 0 | 1.59576e+08 | True |
| leak.control.numeric_normalization.n10000.csv / full_reference / standard | 1 | 2.85833 | 0 | 1.7254e+08 | True |
| leak.control.numeric_normalization.n10000.pqstr / full_reference / standard | 1 | 3.20374 | 0 | 1.60313e+08 | True |
| leak.control.one_to_many.n10000.csv / full_reference / standard | 1 | 2.49749 | 0 | 1.70897e+08 | True |
| leak.control.one_to_many.n10000.pqstr / full_reference / standard | 1 | 2.79395 | 0 | 1.53772e+08 | True |
| leak.control.support200.csv / full_reference / standard | 1 | 0.266356 | 0 | 1.47886e+08 | True |
| leak.control.support200.pqstr / full_reference / standard | 1 | 0.270868 | 0 | 1.36663e+08 | True |
| leak.control.support49.csv / full_reference / standard | 1 | 0.221899 | 0 | 1.54325e+08 | True |
| leak.control.support49.pqstr / full_reference / standard | 1 | 0.210716 | 0 | 1.38498e+08 | True |
| leak.control.support50.csv / full_reference / standard | 1 | 0.229788 | 0 | 1.5736e+08 | True |
| leak.control.support50.pqstr / full_reference / standard | 1 | 0.20688 | 0 | 1.32551e+08 | True |
| leak.control.zero_pairs.n10000.csv / full_reference / standard | 1 | 2.53865 | 0 | 1.75575e+08 | True |
| leak.control.zero_pairs.n10000.pqstr / full_reference / standard | 1 | 2.75727 | 0 | 1.53448e+08 | True |
| leak.equality.m0.n10000.csv / full_reference / standard | 1 | 2.74595 | 0 | 1.76648e+08 | True |
| leak.equality.m0.n10000.pqstr / full_reference / standard | 1 | 3.05378 | 0 | 1.56348e+08 | True |
| leak.equality.m10000.n10000.csv / full_reference / standard | 1 | 2.75567 | 0 | 1.79442e+08 | True |
| leak.equality.m10000.n10000.pqstr / full_reference / standard | 1 | 3.03245 | 0 | 1.53539e+08 | True |
| leak.equality.m9989.n10000.csv / full_reference / standard | 1 | 2.7545 | 0 | 1.74612e+08 | True |
| leak.equality.m9989.n10000.pqstr / full_reference / standard | 1 | 3.01722 | 0 | 1.53272e+08 | True |
| leak.equality.m9990.n10000.csv / full_reference / standard | 1 | 2.76186 | 0 | 1.72192e+08 | True |
| leak.equality.m9990.n10000.pqstr / full_reference / standard | 1 | 3.08569 | 0 | 1.5643e+08 | True |
| leak.equality.m9991.n10000.csv / full_reference / standard | 1 | 2.79966 | 0 | 1.74789e+08 | True |
| leak.equality.m9991.n10000.pqstr / full_reference / standard | 1 | 3.05785 | 0 | 1.55685e+08 | True |
| leak.mapping.r10000.n10000.csv / full_reference / standard | 1 | 2.41444 | 0 | 1.69087e+08 | True |
| leak.mapping.r10000.n10000.pqstr / full_reference / standard | 1 | 2.70697 | 0 | 1.57405e+08 | True |
| leak.mapping.r9989.n10000.csv / full_reference / standard | 1 | 2.37427 | 0 | 1.74756e+08 | True |
| leak.mapping.r9989.n10000.pqstr / full_reference / standard | 1 | 2.77496 | 0 | 1.5614e+08 | True |
| leak.mapping.r9990.n10000.csv / full_reference / standard | 1 | 2.49593 | 0 | 1.77046e+08 | True |
| leak.mapping.r9990.n10000.pqstr / full_reference / decimal_high | 2 | 2.54565 | 0.00292569 | 1.58116e+08 | True |
| leak.mapping.r9990.n10000.pqstr / full_reference / decimal_low | 2 | 2.62162 | 0.0215084 | 1.55167e+08 | True |
| leak.mapping.r9990.n10000.pqstr / full_reference / hash_fortytwo | 2 | 2.55713 | 0.00458976 | 1.56586e+08 | True |
| leak.mapping.r9990.n10000.pqstr / full_reference / hash_one | 2 | 2.49717 | 0.0120304 | 1.57776e+08 | True |
| leak.mapping.r9990.n10000.pqstr / full_reference / standard | 2 | 2.58757 | 0.0112734 | 1.57934e+08 | True |
| leak.mapping.r9990.n10000.pqstr / full_reference / timezone_berlin | 2 | 2.595 | 0.0062097 | 1.57446e+08 | True |
| leak.mapping.r9991.n10000.csv / full_reference / standard | 1 | 2.43001 | 0 | 1.73228e+08 | True |
| leak.mapping.r9991.n10000.pqstr / full_reference / standard | 1 | 2.76908 | 0 | 1.54305e+08 | True |
| missing.feature.m0.n10000.csv / full_reference / standard | 1 | 1.66259 | 0 | 1.73015e+08 | True |
| missing.feature.m0.n10000.pqstr / full_reference / standard | 1 | 1.85551 | 0 | 1.57966e+08 | True |
| missing.feature.m1000.n10000.csv / full_reference / standard | 1 | 1.61322 | 0 | 1.74768e+08 | True |
| missing.feature.m1000.n10000.pqstr / full_reference / standard | 1 | 1.77481 | 0 | 1.52007e+08 | True |
| missing.feature.m1001.n10000.csv / full_reference / standard | 1 | 1.5947 | 0 | 1.76296e+08 | True |
| missing.feature.m1001.n10000.pqstr / full_reference / standard | 1 | 1.82961 | 0 | 1.56021e+08 | True |
| missing.feature.m2000.n10000.csv / full_reference / standard | 1 | 1.6119 | 0 | 1.70656e+08 | True |
| missing.feature.m2000.n10000.pqstr / full_reference / standard | 1 | 1.7156 | 0 | 1.57557e+08 | True |
| missing.feature.m2999.n10000.csv / full_reference / standard | 1 | 1.57754 | 0 | 1.78061e+08 | True |
| missing.feature.m2999.n10000.pqstr / full_reference / standard | 1 | 1.71755 | 0 | 1.59498e+08 | True |
| missing.feature.m3000.n10000.csv / full_reference / standard | 1 | 1.55266 | 0 | 1.71778e+08 | True |
| missing.feature.m3000.n10000.pqstr / full_reference / standard | 1 | 1.73889 | 0 | 1.61624e+08 | True |
| missing.feature.m3001.n10000.csv / full_reference / standard | 1 | 1.58748 | 0 | 1.6656e+08 | True |
| missing.feature.m3001.n10000.pqstr / full_reference / standard | 1 | 1.71959 | 0 | 1.57471e+08 | True |
| missing.feature.m500.n10000.csv / full_reference / standard | 1 | 1.63571 | 0 | 1.76423e+08 | True |
| missing.feature.m500.n10000.pqstr / full_reference / standard | 1 | 1.80106 | 0 | 1.57807e+08 | True |
| missing.feature.m5000.n10000.csv / full_reference / standard | 1 | 1.55927 | 0 | 1.7136e+08 | True |
| missing.feature.m5000.n10000.pqstr / full_reference / standard | 1 | 1.72487 | 0 | 1.58523e+08 | True |
| missing.feature.m999.n10000.csv / full_reference / standard | 1 | 1.60273 | 0 | 1.76878e+08 | True |
| missing.feature.m999.n10000.pqstr / full_reference / standard | 1 | 1.90753 | 0 | 1.53919e+08 | True |
| missing.target.m0.n10000.csv / full_reference / standard | 1 | 2.41929 | 0 | 1.77418e+08 | True |
| missing.target.m0.n10000.pqstr / full_reference / standard | 1 | 2.71095 | 0 | 1.57356e+08 | True |
| missing.target.m100.n10000.csv / full_reference / standard | 1 | 2.44797 | 0 | 1.70672e+08 | True |
| missing.target.m100.n10000.pqstr / full_reference / decimal_high | 2 | 2.58368 | 0.0148846 | 1.56508e+08 | True |
| missing.target.m100.n10000.pqstr / full_reference / decimal_low | 2 | 2.55417 | 0.0240933 | 1.55728e+08 | True |
| missing.target.m100.n10000.pqstr / full_reference / hash_fortytwo | 2 | 2.69218 | 0.0723034 | 1.55498e+08 | True |
| missing.target.m100.n10000.pqstr / full_reference / hash_one | 2 | 2.59439 | 0.000660204 | 1.58841e+08 | True |
| missing.target.m100.n10000.pqstr / full_reference / standard | 2 | 2.51174 | 0.0199697 | 1.57741e+08 | True |
| missing.target.m100.n10000.pqstr / full_reference / timezone_berlin | 2 | 2.61106 | 0.0339563 | 1.56572e+08 | True |
| missing.target.m101.n10000.csv / full_reference / standard | 1 | 2.45178 | 0 | 1.70525e+08 | True |
| missing.target.m101.n10000.pqstr / full_reference / standard | 1 | 2.71187 | 0 | 1.5804e+08 | True |
| missing.target.m500.n10000.csv / full_reference / standard | 1 | 2.43218 | 0 | 1.76169e+08 | True |
| missing.target.m500.n10000.pqstr / full_reference / standard | 1 | 2.79466 | 0 | 1.5546e+08 | True |
| missing.target.m99.n10000.csv / full_reference / standard | 1 | 2.50229 | 0 | 1.717e+08 | True |
| missing.target.m99.n10000.pqstr / full_reference / standard | 1 | 2.74242 | 0 | 1.55673e+08 | True |
| negative.analytics_entity.n10000.csv / full_reference / standard | 1 | 2.17341 | 0 | 1.79089e+08 | True |
| negative.analytics_entity.n10000.pqstr / full_reference / standard | 1 | 2.30811 | 0 | 1.66343e+08 | True |
| negative.declared_id.n10000.csv / full_reference / standard | 1 | 1.93262 | 0 | 1.76947e+08 | True |
| negative.declared_id.n10000.pqstr / full_reference / standard | 1 | 2.11045 | 0 | 1.66064e+08 | True |
| negative.supervised_target_omitted.n10000.csv / full_reference / standard | 1 | 1.60714 | 0 | 1.69026e+08 | True |
| negative.supervised_target_omitted.n10000.pqstr / full_reference / standard | 1 | 1.80249 | 0 | 1.61993e+08 | True |
| parse.numeric.f0.n10000.csv / full_reference / standard | 1 | 1.61469 | 0 | 1.74563e+08 | True |
| parse.numeric.f0.n10000.pqstr / full_reference / standard | 1 | 1.82798 | 0 | 1.57508e+08 | True |
| parse.numeric.f100.n10000.csv / full_reference / standard | 1 | 1.62973 | 0 | 1.7281e+08 | True |
| parse.numeric.f100.n10000.pqstr / full_reference / standard | 1 | 1.79341 | 0 | 1.56254e+08 | True |
| parse.numeric.f101.n10000.csv / full_reference / standard | 1 | 1.66484 | 0 | 1.7555e+08 | True |
| parse.numeric.f101.n10000.pqstr / full_reference / standard | 1 | 1.83721 | 0 | 1.52117e+08 | True |
| parse.numeric.f1999.n10000.csv / full_reference / standard | 1 | 1.56389 | 0 | 1.69259e+08 | True |
| parse.numeric.f1999.n10000.pqstr / full_reference / standard | 1 | 1.78602 | 0 | 1.55836e+08 | True |
| parse.numeric.f2000.n10000.csv / full_reference / standard | 1 | 1.56729 | 0 | 1.77635e+08 | True |
| parse.numeric.f2000.n10000.pqstr / full_reference / standard | 1 | 1.78412 | 0 | 1.60649e+08 | True |
| parse.numeric.f2001.n10000.csv / full_reference / decimal_high | 2 | 1.54416 | 0.0176731 | 1.75192e+08 | True |
| parse.numeric.f2001.n10000.csv / full_reference / decimal_low | 2 | 1.5269 | 0.00520925 | 1.76415e+08 | True |
| parse.numeric.f2001.n10000.csv / full_reference / hash_fortytwo | 2 | 1.57895 | 0.0202005 | 1.74414e+08 | True |
| parse.numeric.f2001.n10000.csv / full_reference / hash_one | 2 | 1.58143 | 0.0317347 | 1.71696e+08 | True |
| parse.numeric.f2001.n10000.csv / full_reference / standard | 2 | 1.54696 | 0.013897 | 1.76511e+08 | True |
| parse.numeric.f2001.n10000.csv / full_reference / timezone_berlin | 2 | 1.4697 | 0.0145199 | 1.74326e+08 | True |
| parse.numeric.f2001.n10000.pqstr / full_reference / standard | 1 | 1.78683 | 0 | 1.52953e+08 | True |
| parse.numeric.f4000.n10000.csv / full_reference / standard | 1 | 1.64746 | 0 | 1.71209e+08 | True |
| parse.numeric.f4000.n10000.pqstr / full_reference / standard | 1 | 1.72008 | 0 | 1.5607e+08 | True |
| parse.numeric.f499.n10000.csv / full_reference / standard | 1 | 1.6192 | 0 | 1.74322e+08 | True |
| parse.numeric.f499.n10000.pqstr / full_reference / standard | 1 | 1.78527 | 0 | 1.53743e+08 | True |
| parse.numeric.f500.n10000.csv / full_reference / standard | 1 | 1.60535 | 0 | 1.71975e+08 | True |
| parse.numeric.f500.n10000.pqstr / full_reference / standard | 1 | 1.82055 | 0 | 1.55849e+08 | True |
| parse.numeric.f501.n10000.csv / full_reference / standard | 1 | 1.62624 | 0 | 1.75722e+08 | True |
| parse.numeric.f501.n10000.pqstr / full_reference / standard | 1 | 1.82216 | 0 | 1.58269e+08 | True |
| parse.numeric.f6000.n10000.csv / full_reference / standard | 1 | 1.55515 | 0 | 1.73109e+08 | True |
| parse.numeric.f6000.n10000.pqstr / full_reference / standard | 1 | 1.74212 | 0 | 1.53084e+08 | True |
| parse.numeric.f99.n10000.csv / full_reference / standard | 1 | 1.63214 | 0 | 1.73335e+08 | True |
| parse.numeric.f99.n10000.pqstr / full_reference / standard | 1 | 1.81674 | 0 | 1.5591e+08 | True |
| sampling.cardinality.gaps.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 47.7108 | 0 | 3.40054e+08 | True |
| sampling.cardinality.gaps.n300000.pqstr / full_reference / standard | 1 | 59.4661 | 0 | 5.04476e+08 | True |
| sampling.cardinality.head.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 49.837 | 0 | 3.36835e+08 | True |
| sampling.cardinality.head.n300000.pqstr / full_reference / standard | 1 | 56.7869 | 0 | 5.03001e+08 | True |
| sampling.cardinality.middle.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 55.9328 | 0 | 3.42757e+08 | True |
| sampling.cardinality.middle.n300000.pqstr / full_reference / standard | 1 | 60.4651 | 0 | 5.04758e+08 | True |
| sampling.cardinality.tail.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 49.7791 | 0 | 3.40918e+08 | True |
| sampling.cardinality.tail.n300000.pqstr / full_reference / standard | 1 | 59.9335 | 0 | 5.05225e+08 | True |
| sampling.class_boundary.gaps.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 64.8755 | 0 | 3.18439e+08 | True |
| sampling.class_boundary.gaps.n300000.pqstr / full_reference / standard | 1 | 73.1444 | 0 | 4.2716e+08 | True |
| sampling.class_boundary.head.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 60.0552 | 0 | 3.15593e+08 | True |
| sampling.class_boundary.head.n300000.pqstr / full_reference / standard | 1 | 70.6046 | 0 | 4.23006e+08 | True |
| sampling.class_boundary.middle.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 61.0968 | 0 | 3.16576e+08 | True |
| sampling.class_boundary.middle.n300000.pqstr / full_reference / standard | 1 | 73.4933 | 0 | 4.29998e+08 | True |
| sampling.class_boundary.tail.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 61.9022 | 0 | 3.16588e+08 | True |
| sampling.class_boundary.tail.n300000.pqstr / full_reference / standard | 1 | 73.7156 | 0 | 4.23879e+08 | True |
| sampling.class_rare.gaps.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 62.2055 | 0 | 3.14982e+08 | True |
| sampling.class_rare.gaps.n300000.pqstr / full_reference / standard | 1 | 69.5616 | 0 | 4.22154e+08 | True |
| sampling.class_rare.head.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 57.7351 | 0 | 3.17604e+08 | True |
| sampling.class_rare.head.n300000.pqstr / full_reference / standard | 1 | 68.447 | 0 | 4.24501e+08 | True |
| sampling.class_rare.middle.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 60.3889 | 0 | 3.13217e+08 | True |
| sampling.class_rare.middle.n300000.pqstr / full_reference / standard | 1 | 71.092 | 0 | 4.2471e+08 | True |
| sampling.class_rare.tail.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 63.1354 | 0 | 3.16269e+08 | True |
| sampling.class_rare.tail.n300000.pqstr / full_reference / standard | 1 | 75.1337 | 0 | 4.21073e+08 | True |
| sampling.duplicate_keys.gaps.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 55.6865 | 0 | 3.8144e+08 | True |
| sampling.duplicate_keys.gaps.n300000.pqstr / full_reference / standard | 1 | 66.0843 | 0 | 5.98708e+08 | True |
| sampling.duplicate_keys.head.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 55.7471 | 0 | 3.78249e+08 | True |
| sampling.duplicate_keys.head.n300000.pqstr / full_reference / standard | 1 | 66.1737 | 0 | 6.02407e+08 | True |
| sampling.duplicate_keys.middle.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 56.6627 | 0 | 3.82816e+08 | True |
| sampling.duplicate_keys.middle.n300000.pqstr / full_reference / standard | 1 | 68.3675 | 0 | 5.97156e+08 | True |
| sampling.duplicate_keys.tail.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 56.422 | 0 | 3.81321e+08 | True |
| sampling.duplicate_keys.tail.n300000.pqstr / full_reference / standard | 1 | 68.3217 | 0 | 6.04815e+08 | True |
| sampling.duplicate_rows.gaps.n300000.pqstr / HEAD_STRIDE_V1 / decimal_high | 2 | 43.2109 | 0.0459657 | 3.29994e+08 | True |
| sampling.duplicate_rows.gaps.n300000.pqstr / HEAD_STRIDE_V1 / decimal_low | 2 | 42.9076 | 0.0445965 | 3.30158e+08 | True |
| sampling.duplicate_rows.gaps.n300000.pqstr / HEAD_STRIDE_V1 / hash_fortytwo | 2 | 40.9125 | 0.151602 | 3.2793e+08 | True |
| sampling.duplicate_rows.gaps.n300000.pqstr / HEAD_STRIDE_V1 / hash_one | 2 | 41.0814 | 0.472046 | 3.2913e+08 | True |
| sampling.duplicate_rows.gaps.n300000.pqstr / HEAD_STRIDE_V1 / standard | 2 | 41.302 | 0.29492 | 3.25095e+08 | True |
| sampling.duplicate_rows.gaps.n300000.pqstr / HEAD_STRIDE_V1 / timezone_berlin | 2 | 42.2655 | 0.732192 | 3.29087e+08 | True |
| sampling.duplicate_rows.gaps.n300000.pqstr / full_reference / standard | 1 | 52.0689 | 0 | 4.29404e+08 | True |
| sampling.duplicate_rows.head.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 42.0805 | 0 | 3.25399e+08 | True |
| sampling.duplicate_rows.head.n300000.pqstr / full_reference / standard | 1 | 51.5689 | 0 | 4.32935e+08 | True |
| sampling.duplicate_rows.middle.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 47.6797 | 0 | 3.27455e+08 | True |
| sampling.duplicate_rows.middle.n300000.pqstr / full_reference / standard | 1 | 58.3912 | 0 | 4.39955e+08 | True |
| sampling.duplicate_rows.tail.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 49.0438 | 0 | 3.30523e+08 | True |
| sampling.duplicate_rows.tail.n300000.pqstr / full_reference / standard | 1 | 60.9533 | 0 | 4.39194e+08 | True |
| sampling.group.gaps.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 93.6915 | 0 | 3.83025e+08 | True |
| sampling.group.gaps.n300000.pqstr / full_reference / standard | 1 | 112.008 | 0 | 5.99278e+08 | True |
| sampling.group.head.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 93.0858 | 0 | 3.82792e+08 | True |
| sampling.group.head.n300000.pqstr / full_reference / standard | 1 | 116.771 | 0 | 5.97311e+08 | True |
| sampling.group.middle.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 80.739 | 0 | 3.80678e+08 | True |
| sampling.group.middle.n300000.pqstr / full_reference / standard | 1 | 102.876 | 0 | 5.97754e+08 | True |
| sampling.group.tail.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 79.904 | 0 | 3.85503e+08 | True |
| sampling.group.tail.n300000.pqstr / full_reference / standard | 1 | 98.477 | 0 | 6.04959e+08 | True |
| sampling.leakage.gaps.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 73.092 | 0 | 3.41201e+08 | True |
| sampling.leakage.gaps.n300000.pqstr / full_reference / standard | 1 | 90.9729 | 0 | 4.80973e+08 | True |
| sampling.leakage.head.n300000.pqstr / HEAD_STRIDE_V1 / decimal_high | 2 | 72.0885 | 0.128755 | 3.38743e+08 | True |
| sampling.leakage.head.n300000.pqstr / HEAD_STRIDE_V1 / decimal_low | 2 | 72.6043 | 0.00391925 | 3.39237e+08 | True |
| sampling.leakage.head.n300000.pqstr / HEAD_STRIDE_V1 / hash_fortytwo | 2 | 75.9139 | 0.614165 | 3.39487e+08 | True |
| sampling.leakage.head.n300000.pqstr / HEAD_STRIDE_V1 / hash_one | 2 | 75.8349 | 0.602853 | 3.39159e+08 | True |
| sampling.leakage.head.n300000.pqstr / HEAD_STRIDE_V1 / standard | 2 | 74.761 | 0.504148 | 3.35112e+08 | True |
| sampling.leakage.head.n300000.pqstr / HEAD_STRIDE_V1 / timezone_berlin | 2 | 74.3858 | 1.0128 | 3.36054e+08 | True |
| sampling.leakage.head.n300000.pqstr / full_reference / standard | 1 | 88.3217 | 0 | 4.79498e+08 | True |
| sampling.leakage.middle.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 71.7167 | 0 | 3.35065e+08 | True |
| sampling.leakage.middle.n300000.pqstr / full_reference / standard | 1 | 87.7644 | 0 | 4.81927e+08 | True |
| sampling.leakage.tail.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 71.5383 | 0 | 3.41189e+08 | True |
| sampling.leakage.tail.n300000.pqstr / full_reference / standard | 1 | 86.7262 | 0 | 4.80887e+08 | True |
| sampling.missingness.gaps.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 40.5504 | 0 | 3.22183e+08 | True |
| sampling.missingness.gaps.n300000.pqstr / full_reference / standard | 1 | 48.0949 | 0 | 4.35036e+08 | True |
| sampling.missingness.head.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 40.6399 | 0 | 3.2725e+08 | True |
| sampling.missingness.head.n300000.pqstr / full_reference / standard | 1 | 48.0706 | 0 | 4.4313e+08 | True |
| sampling.missingness.middle.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 40.7033 | 0 | 3.19365e+08 | True |
| sampling.missingness.middle.n300000.pqstr / full_reference / standard | 1 | 47.9922 | 0 | 4.30805e+08 | True |
| sampling.missingness.tail.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 40.0798 | 0 | 3.2539e+08 | True |
| sampling.missingness.tail.n300000.pqstr / full_reference / standard | 1 | 47.3242 | 0 | 4.40099e+08 | True |
| sampling.parse.gaps.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 41.2756 | 0 | 3.28647e+08 | True |
| sampling.parse.gaps.n300000.pqstr / full_reference / standard | 1 | 49.0703 | 0 | 4.40877e+08 | True |
| sampling.parse.head.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 41.4952 | 0 | 3.29748e+08 | True |
| sampling.parse.head.n300000.pqstr / full_reference / standard | 1 | 49.2005 | 0 | 4.40504e+08 | True |
| sampling.parse.middle.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 41.1714 | 0 | 3.30387e+08 | True |
| sampling.parse.middle.n300000.pqstr / full_reference / standard | 1 | 49.7225 | 0 | 4.40566e+08 | True |
| sampling.parse.tail.n300000.pqstr / HEAD_STRIDE_V1 / standard | 1 | 41.5043 | 0 | 3.27156e+08 | True |
| sampling.parse.tail.n300000.pqstr / full_reference / standard | 1 | 49.4437 | 0 | 4.42438e+08 | True |
| scale.analytics.n10000.w20.csv / scale_default / standard | 3 | 4.96495 | 0.0120034 | 1.95764e+08 | True |
| scale.analytics.n10000.w20.pqnative / scale_default / standard | 3 | 4.19353 | 0.0166786 | 1.71057e+08 | True |
| scale.analytics.n10000.w300.csv / scale_default / standard | 3 | 175.138 | 0.201802 | 7.14936e+08 | True |
| scale.analytics.n10000.w300.pqnative / scale_default / standard | 3 | 75.6459 | 0.153742 | 5.31862e+08 | True |
| scale.analytics.n100000.w100.csv / scale_default / standard | 3 | 352.52 | 0.649731 | 9.02177e+08 | True |
| scale.analytics.n100000.w100.pqnative / scale_default / standard | 3 | 239.105 | 1.37081 | 7.01686e+08 | True |
| scale.analytics.n100000.w20.csv / scale_default / standard | 3 | 53.1748 | 0.181894 | 5.13769e+08 | True |
| scale.analytics.n100000.w20.pqnative / scale_default / standard | 3 | 44.9321 | 0.0865563 | 4.25001e+08 | True |
| scale.analytics.n1000000.w100.pqnative / scale_default / standard | 3 | 1148.83 | 13.365 | 7.26114e+08 | True |
| scale.analytics.n1000000.w20.csv / scale_default / standard | 3 | 269.662 | 0.265799 | 8.30075e+08 | True |
| scale.analytics.n1000000.w20.pqnative / scale_default / standard | 3 | 225.793 | 2.29293 | 6.51194e+08 | True |
| scale.analytics.n5000000.w20.pqnative / scale_default / standard | 2 | 912.231 | 1.82148 | 6.68486e+08 | True |
| scale.regression.n100000.w20.pqnative / scale_default / standard | 3 | 63.9351 | 0.401964 | 4.15404e+08 | True |
| scale.regression.n1000000.w20.pqnative / scale_default / standard | 3 | 324.772 | 1.96956 | 6.3821e+08 | True |
| split.analytics_random_valid.n10000.csv / full_reference / standard | 1 | 1.58841 | 0 | 1.72839e+08 | True |
| split.analytics_random_valid.n10000.pqstr / full_reference / standard | 1 | 1.80578 | 0 | 1.60444e+08 | True |
| split.reg_random_degraded.n10000.csv / full_reference / standard | 1 | 2.62654 | 0 | 1.78962e+08 | True |
| split.reg_random_degraded.n10000.pqstr / full_reference / standard | 1 | 2.92057 | 0 | 1.6325e+08 | True |
| split.reg_random_valid.n10000.csv / full_reference / standard | 1 | 2.6222 | 0 | 1.80158e+08 | True |
| split.reg_random_valid.n10000.pqstr / full_reference / standard | 1 | 2.95126 | 0 | 1.62062e+08 | True |
| split.reg_time_valid.n10000.csv / full_reference / standard | 1 | 2.67238 | 0 | 1.72978e+08 | True |
| split.reg_time_valid.n10000.pqstr / full_reference / standard | 1 | 2.90009 | 0 | 1.60944e+08 | True |
| split.ts_group.n10000.csv / full_reference / standard | 1 | 3.01328 | 0 | 1.74727e+08 | True |
| split.ts_group.n10000.pqstr / full_reference / standard | 1 | 3.31422 | 0 | 1.68423e+08 | True |
| split.ts_random.n10000.csv / full_reference / standard | 1 | 2.56953 | 0 | 1.70652e+08 | True |
| split.ts_random.n10000.pqstr / full_reference / standard | 1 | 2.90623 | 0 | 1.61706e+08 | True |
| timestamp.regression.absent.n10000.csv / full_reference / standard | 1 | 2.48744 | 0 | 1.74895e+08 | True |
| timestamp.regression.absent.n10000.pqstr / full_reference / standard | 1 | 2.7035 | 0 | 1.56049e+08 | True |
| timestamp.regression.valid0.n10000.csv / full_reference / standard | 1 | 2.63075 | 0 | 1.73048e+08 | True |
| timestamp.regression.valid0.n10000.pqstr / full_reference / standard | 1 | 2.80273 | 0 | 1.52187e+08 | True |
| timestamp.regression.valid10000.n10000.csv / full_reference / standard | 1 | 2.6023 | 0 | 1.68518e+08 | True |
| timestamp.regression.valid10000.n10000.pqstr / full_reference / standard | 1 | 2.8821 | 0 | 1.57962e+08 | True |
| timestamp.regression.valid7999.n10000.csv / full_reference / standard | 1 | 2.60437 | 0 | 1.72511e+08 | True |
| timestamp.regression.valid7999.n10000.pqstr / full_reference / standard | 1 | 2.88339 | 0 | 1.61448e+08 | True |
| timestamp.regression.valid8000.n10000.csv / full_reference / standard | 1 | 2.55676 | 0 | 1.64352e+08 | True |
| timestamp.regression.valid8000.n10000.pqstr / full_reference / standard | 1 | 2.90406 | 0 | 1.57606e+08 | True |
| timestamp.regression.valid8001.n10000.csv / full_reference / standard | 1 | 2.67463 | 0 | 1.72499e+08 | True |
| timestamp.regression.valid8001.n10000.pqstr / full_reference / standard | 1 | 2.9461 | 0 | 1.63783e+08 | True |
| timestamp.regression.valid9499.n10000.csv / full_reference / standard | 1 | 2.63663 | 0 | 1.73867e+08 | True |
| timestamp.regression.valid9499.n10000.pqstr / full_reference / standard | 1 | 2.8589 | 0 | 1.65315e+08 | True |
| timestamp.regression.valid9500.n10000.csv / full_reference / standard | 1 | 2.60198 | 0 | 1.71786e+08 | True |
| timestamp.regression.valid9500.n10000.pqstr / full_reference / standard | 1 | 2.83824 | 0 | 1.6459e+08 | True |
| timestamp.regression.valid9501.n10000.csv / full_reference / standard | 1 | 2.52541 | 0 | 1.76234e+08 | True |
| timestamp.regression.valid9501.n10000.pqstr / full_reference / standard | 1 | 2.93427 | 0 | 1.64778e+08 | True |
| timestamp.time_series.absent.n10000.csv / full_reference / standard | 1 | 2.49033 | 0 | 1.6896e+08 | True |
| timestamp.time_series.absent.n10000.pqstr / full_reference / standard | 1 | 2.75905 | 0 | 1.54206e+08 | True |
| timestamp.time_series.valid0.n10000.csv / full_reference / standard | 1 | 2.71791 | 0 | 1.76103e+08 | True |
| timestamp.time_series.valid0.n10000.pqstr / full_reference / standard | 1 | 2.8198 | 0 | 1.53469e+08 | True |
| timestamp.time_series.valid10000.n10000.csv / full_reference / standard | 1 | 2.59747 | 0 | 1.73515e+08 | True |
| timestamp.time_series.valid10000.n10000.pqstr / full_reference / standard | 1 | 2.82218 | 0 | 1.5763e+08 | True |
| timestamp.time_series.valid7999.n10000.csv / full_reference / standard | 1 | 2.59703 | 0 | 1.80437e+08 | True |
| timestamp.time_series.valid7999.n10000.pqstr / full_reference / standard | 1 | 2.94369 | 0 | 1.61509e+08 | True |
| timestamp.time_series.valid8000.n10000.csv / full_reference / standard | 1 | 2.61428 | 0 | 1.75018e+08 | True |
| timestamp.time_series.valid8000.n10000.pqstr / full_reference / standard | 1 | 2.82423 | 0 | 1.63344e+08 | True |
| timestamp.time_series.valid8001.n10000.csv / full_reference / standard | 1 | 2.59001 | 0 | 1.71835e+08 | True |
| timestamp.time_series.valid8001.n10000.pqstr / full_reference / standard | 1 | 2.94752 | 0 | 1.57487e+08 | True |
| timestamp.time_series.valid9499.n10000.csv / full_reference / standard | 1 | 2.59967 | 0 | 1.71872e+08 | True |
| timestamp.time_series.valid9499.n10000.pqstr / full_reference / standard | 1 | 2.84109 | 0 | 1.65093e+08 | True |
| timestamp.time_series.valid9500.n10000.csv / full_reference / standard | 1 | 2.58667 | 0 | 1.74989e+08 | True |
| timestamp.time_series.valid9500.n10000.pqstr / full_reference / standard | 1 | 2.83424 | 0 | 1.64811e+08 | True |
| timestamp.time_series.valid9501.n10000.csv / full_reference / standard | 1 | 2.58676 | 0 | 1.73793e+08 | True |
| timestamp.time_series.valid9501.n10000.pqstr / full_reference / standard | 1 | 2.92086 | 0 | 1.62922e+08 | True |

Warmups are retained in runs.jsonl and excluded from aggregates. MAD is the median absolute deviation. Canonical report disagreement is a determinism failure.

See [determinism](tables/determinism.csv) and [first mismatch paths](tables/mismatch_paths.csv). Original byte disagreements remain visible even when parsed report fields agree. No target report is normalized to manufacture agreement.

## Sampling fidelity and scalability

Variants and scale points are explicit in the manifest. This summary does not infer full-versus-sampled fidelity or scaling behavior from unrelated scenarios.

[Sampling fidelity](tables/sampling_fidelity.csv) and [primitive counts](tables/sampling_primitives.csv) report bounded-minus-full differences, including unavailable reasons. [Format equivalence](tables/format_equivalence.csv) separates strict string transports from native semantic-projection eligibility. [Scale performance](tables/scale_performance.csv) retains raw repeats, medians, ranges, unscaled MAD and explicit two-run weak evidence. Missing target outcomes have no invented timings.

## Failure cases and limitations

Terminal coverage (including warmups): 578 successful reports; 0 adverse target outcomes retained in failures.jsonl. Failed analyses contribute no invented scores or performance values.

Report availability is determined only by the selected scientific outcome. Resolved infrastructure retries remain operational history. Missing reports remain visible in the detection and clean-control coverage columns; high conditional agreement with incomplete coverage must not be interpreted as complete detection.

Operational history only: 578 attempts, 0 infrastructure retries, 0 resolved infrastructure failures. attempts.jsonl preserves every attempt; runs.jsonl/failures.jsonl contain only the first valid selected outcome. Retries never increase scientific support or performance repeat counts.

Unexpected outcomes remain in the raw records. Synthetic cases cannot establish real-world prevalence, model quality or production guarantees. Sampled RSS can miss short peaks. Review outcomes before drawing scientific conclusions.

## Reproduction

Use the exact benchmark revision and fingerprinted target artifact, dependency versions in environment.json, scenario snapshots and run_specs.json. Verify checksums before analysis. Execution requires a resolved ready manifest and a verified working ledger.

## Generated artifact queries

- [clean_false_positives.csv](tables/clean_false_positives.csv)
- [composite_interactions.csv](tables/composite_interactions.csv)
- [detection_by_check.csv](tables/detection_by_check.csv)
- [determinism.csv](tables/determinism.csv)
- [failures.csv](tables/failures.csv)
- [format_equivalence.csv](tables/format_equivalence.csv)
- [identity.csv](tables/identity.csv)
- [mismatch_paths.csv](tables/mismatch_paths.csv)
- [remediation.csv](tables/remediation.csv)
- [sampling_fidelity.csv](tables/sampling_fidelity.csv)
- [sampling_primitives.csv](tables/sampling_primitives.csv)
- [scale_performance.csv](tables/scale_performance.csv)
- [scenario_matrix.csv](tables/scenario_matrix.csv)
- [score_sweeps.csv](tables/score_sweeps.csv)
- [threshold_boundaries.csv](tables/threshold_boundaries.csv)

![clean false positives](figures/clean_false_positives.svg)

![detection by check](figures/detection_by_check.svg)

![peak rss vs rows](figures/peak_rss_vs_rows.svg)

![runtime vs rows](figures/runtime_vs_rows.svg)

![sampling finding agreement](figures/sampling_finding_agreement.svg)

![sampling score delta](figures/sampling_score_delta.svg)

![score class imbalance](figures/score_class_imbalance.svg)

![score duplicates](figures/score_duplicates.svg)

![score leakage](figures/score_leakage.svg)

![score missingness](figures/score_missingness.svg)

![throughput vs rows](figures/throughput_vs_rows.svg)
