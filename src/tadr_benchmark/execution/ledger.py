"""Exclusive, append-only local attempt journal with verified resume bindings."""

import json
import os
from pathlib import Path

from ..companions import InstrumentationRecord, RunFailure
from ..models import RunResult, RunSpec
from ..serialization import canonical_bytes, sha256
from .attempts import AttemptRecord, attempt_id, make_attempt, validate_attempts


def write_once(path: Path, data: bytes) -> None:
    """Publish a flushed file atomically while the ledger's exclusive lock is held."""
    if path.exists():
        raise ValueError("immutable working artifact already exists")
    temporary = path.with_suffix(path.suffix + ".pending")
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


class RunLedger:
    """Hold the context manager throughout execution; OS locks survive no crash.

    A reservation left by interruption becomes a visible unresolved infrastructure
    attempt. Resolution is an additional immutable receipt, never a rewritten result.
    """

    def __init__(self, directory: Path, specs: list[RunSpec], binding: dict):
        self.directory, self.specs = directory, specs
        self.binding = canonical_bytes({"run_specs": [s.model_dump(mode="json") for s in specs],
                                        "provenance": binding})
        self._lock = None

    def __enter__(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = (self.directory / ".lock").open("a+b")
        try:
            self._lock.seek(0)
            if os.name == "nt":
                import msvcrt
                if self._lock.read(1) == b"":
                    self._lock.write(b"0")
                    self._lock.flush()
                self._lock.seek(0)
                msvcrt.locking(self._lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            path = self.directory / "binding.json"
            if path.exists():
                if path.read_bytes() != self.binding:
                    raise ValueError("resume provenance/hash mismatch")
            else:
                write_once(path, self.binding)
            self.snapshot()
            return self
        except BaseException:
            self._lock.close()
            self._lock = None
            raise

    def __exit__(self, *args):
        self._lock.close()
        self._lock = None

    def _require_lock(self):
        if self._lock is None:
            raise RuntimeError("ledger operations require an exclusive session")

    def snapshot(self) -> list[AttemptRecord]:
        self._require_lock()
        attempts = []
        for path in sorted(self.directory.glob("attempt.*")):
            reservation = RunFailure.model_validate_json((path / "reservation.json").read_bytes())
            outcome_path = path / "outcome.json"
            if outcome_path.exists():
                payload = outcome_path.read_bytes()
                completion = json.loads((path / "completion.json").read_bytes())
                names = {"reservation.json", "outcome.json", "instrumentation.json"}
                if "failure_kind" not in json.loads(payload):
                    names.add("report.json")
                if set(completion) != names or any(sha256((path / name).read_bytes()) != digest
                                                   for name, digest in completion.items()):
                    raise ValueError("working completion checksum mismatch")
                outcome = (RunFailure if "failure_kind" in json.loads(payload) else RunResult).model_validate_json(payload)
            else:
                outcome = reservation
            # A completion may change terminal fields, never the reserved provenance.
            fields = set(RunFailure.model_fields) - {
                "failure_kind", "stage", "error_code", "exception_class", "adjudication",
                "independently_validated_input", "elapsed_seconds", "policy_limit"}
            if any(getattr(outcome, f) != getattr(reservation, f) for f in fields):
                raise ValueError("completed attempt differs from reserved provenance")
            if isinstance(outcome, RunResult):
                if sha256((path / "report.json").read_bytes()) != outcome.canonical_report_sha256:
                    raise ValueError("working report checksum mismatch")
            elif (path / "report.json").exists() and outcome_path.exists():
                raise ValueError("failed attempt has an unexpected report")
            monitor_path = path / "instrumentation.json"
            monitor = InstrumentationRecord.model_validate_json(monitor_path.read_bytes()) if monitor_path.exists() else None
            resolution_path = path / "resolution.json"
            resolution = json.loads(resolution_path.read_bytes()) if resolution_path.exists() else None
            index = int(path.name.rsplit(".", 1)[1])
            attempt = make_attempt(outcome, index, monitor,
                                   resolution_code=resolution["resolution_code"] if resolution else None)
            if path.name != attempt.attempt_id:
                raise ValueError("attempt directory identity mismatch")
            if resolution and resolution != {"attempt_id": attempt.attempt_id,
                    "outcome_sha256": attempt.outcome_sha256, "resolution_code": attempt.resolution_code}:
                raise ValueError("resolution receipt does not bind the failed attempt")
            attempts.append(attempt)
        selected = [a.outcome for a in attempts if a.selected_as_final_outcome]
        validate_attempts(self.specs, attempts, [o for o in selected if isinstance(o, RunResult)],
                          [o for o in selected if isinstance(o, RunFailure)], complete=False)
        return attempts

    def begin(self, interruption_outcome: RunFailure) -> str:
        if interruption_outcome.failure_kind != "infrastructure":
            raise ValueError("reservation must describe an interrupted infrastructure attempt")
        history = [a for a in self.snapshot() if a.run_id == interruption_outcome.run_id]
        if any(a.selected_as_final_outcome for a in history):
            raise ValueError("validated completed work must not be rerun")
        if any(a.infrastructure_resolution_status != "resolved" for a in history):
            raise ValueError("retry requires explicit infrastructure resolution")
        attempt = make_attempt(interruption_outcome, len(history))
        # Validate identity and provenance before adding anything to the journal.
        all_attempts = self.snapshot() + [attempt]
        selected = [a.outcome for a in all_attempts if a.selected_as_final_outcome]
        validate_attempts(self.specs, all_attempts, [o for o in selected if isinstance(o, RunResult)],
                          [o for o in selected if isinstance(o, RunFailure)], complete=False)
        path = self.directory / attempt.attempt_id
        path.mkdir()
        write_once(path / "reservation.json", canonical_bytes(interruption_outcome))
        return attempt.attempt_id

    def complete(self, identity: str, outcome: RunResult | RunFailure,
                 instrumentation: InstrumentationRecord, report: bytes | None = None) -> None:
        histories = {a.attempt_id: a for a in self.snapshot()}
        if identity not in histories:
            raise ValueError("attempt was not reserved")
        prior = histories[identity]
        if prior.infrastructure_resolution_status == "resolved":
            raise ValueError("resolved interrupted attempt cannot complete later")
        candidate = make_attempt(outcome, prior.attempt_index, instrumentation)
        fields = set(RunFailure.model_fields) - {
            "failure_kind", "stage", "error_code", "exception_class", "adjudication",
            "independently_validated_input", "elapsed_seconds", "policy_limit"}
        if any(getattr(outcome, f) != getattr(prior.outcome, f) for f in fields):
            raise ValueError("completion provenance differs from reservation")
        attempts = [candidate if a.attempt_id == identity else a for a in histories.values()]
        selected = [a.outcome for a in attempts if a.selected_as_final_outcome]
        validate_attempts(self.specs, attempts, [o for o in selected if isinstance(o, RunResult)],
                          [o for o in selected if isinstance(o, RunFailure)], complete=False)
        if isinstance(outcome, RunResult):
            if report is None or sha256(report) != outcome.canonical_report_sha256:
                raise ValueError("original report bytes do not match outcome")
        elif report is not None:
            raise ValueError("failure cannot have a successful report")
        path = self.directory / identity
        if report is not None:
            write_once(path / "report.json", report)
        write_once(path / "instrumentation.json", canonical_bytes(instrumentation))
        payload = canonical_bytes(outcome)
        completion = {name: sha256((path / name).read_bytes()) for name in ("reservation.json", "instrumentation.json")}
        completion["outcome.json"] = sha256(payload)
        if report is not None:
            completion["report.json"] = sha256(report)
        write_once(path / "completion.json", canonical_bytes(completion))
        # The outcome is the final transaction marker. Interrupted prior writes
        # retain a reservation and cannot be mistaken for completed measurements.
        write_once(path / "outcome.json", payload)
        self.snapshot()

    def resolve(self, identity: str, resolution_code: str) -> None:
        histories = {a.attempt_id: a for a in self.snapshot()}
        if identity not in histories:
            raise ValueError("unknown infrastructure attempt")
        prior = histories[identity]
        candidate = make_attempt(prior.outcome, prior.attempt_index, prior.instrumentation,
                                 resolution_code=resolution_code)
        write_once(self.directory / identity / "resolution.json", canonical_bytes({
            "attempt_id": identity, "outcome_sha256": candidate.outcome_sha256,
            "resolution_code": resolution_code}))

    def selected(self, run_id: str) -> RunResult | RunFailure | None:
        return next((a.outcome for a in self.snapshot()
                     if a.run_id == run_id and a.selected_as_final_outcome), None)
