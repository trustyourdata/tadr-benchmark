"""Pinned public report rate representation; never rewrites observed reports."""

from decimal import Decimal, ROUND_HALF_EVEN, localcontext


def canonical_report_rate(value: Decimal | float | int) -> Decimal:
    """Round an expected rate using the public four-place, half-even contract."""
    value = value if isinstance(value, Decimal) else Decimal(str(value))
    if not value.is_finite() or not 0 <= value <= 1:
        raise ValueError("report rate must be finite and between zero and one")
    with localcontext() as context:
        context.prec = 50
        return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)


def expected_sampling_observation(variant: str) -> tuple[str, float]:
    """Alpha's declared counts expressed at public report precision."""
    if variant == "full_reference":
        return "full", float(canonical_report_rate(1))
    if variant != "HEAD_STRIDE_V1":
        raise ValueError("unregistered Alpha sampling variant")
    with localcontext() as context:
        context.prec = 50
        expected = Decimal(200000) / Decimal(300000)
    return "sampled", float(canonical_report_rate(expected))


def validate_sampling_observation(variant: str, mode: str, ratio: float) -> None:
    # Only the expectation is canonicalized. Noncanonical observed values must
    # fail; rounding observations would silently accept a different report.
    if (mode, ratio) != expected_sampling_observation(variant):
        raise ValueError("sampling mode/ratio violates protocol")
