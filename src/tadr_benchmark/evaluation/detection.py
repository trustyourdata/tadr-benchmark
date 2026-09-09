from fnmatch import fnmatchcase

from ..models import DetectionOutcome, GroundTruth


def evaluate(truth: GroundTruth, finding_ids: list[str], finding_subjects: list[str],
             hard_gates: list[str]) -> DetectionOutcome:
    if len(finding_ids) != len(finding_subjects):
        raise ValueError("unaligned Finding subjects")

    def matches(expectation, index):
        return (fnmatchcase(finding_ids[index], expectation.id_pattern)
                and (expectation.subject is None or expectation.subject == finding_subjects[index]))

    matched = [i for i, item in enumerate(truth.expected_findings)
               if any(matches(item, j) for j in range(len(finding_ids)))]
    absent = [i for i, item in enumerate(truth.expected_absent_findings)
              if any(matches(item, j) for j in range(len(finding_ids)))]
    unexpected = sorted(finding_ids[j] for j in range(len(finding_ids))
                        if not any(matches(item, j) for item in truth.expected_findings))
    gate = None if truth.expected_gate_behavior == "unconstrained" else (
        bool(hard_gates) == (truth.expected_gate_behavior == "present"))
    return DetectionOutcome(matched_expectations=matched,
                            missed_expectations=[i for i in range(len(truth.expected_findings)) if i not in matched],
                            violated_absent_expectations=absent,
                            unexpected_finding_ids=unexpected, gate_expectation_met=gate)
