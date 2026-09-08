"""Apply and independently acknowledge context before target import."""

import decimal
import os
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ..models import Contract, DeterminismCase
from typing import Literal


class ContextAcknowledgement(Contract):
    case: DeterminismCase
    hash_seed_verified: bool
    timezone_verified: bool
    timezone_method: Literal["tzset", "startup_environment"]
    decimal_verified: bool
    polars_max_threads: Literal[4] = 4
    target_not_imported: bool


def apply_context(case: DeterminismCase) -> ContextAcknowledgement:
    if "tadr" in sys.modules or any(name.startswith("tadr.") for name in sys.modules):
        raise ValueError("target imported before context")
    # Hash seeding must be passed to process creation, never changed here.
    if os.environ.get("PYTHONHASHSEED") != str(case.python_hash_seed):
        raise ValueError("hash seed was not supplied at process startup")
    if os.environ.get("POLARS_MAX_THREADS") != "4":
        raise ValueError("Polars thread setting differs from protocol")
    if os.environ.get("TZ") != case.timezone:
        raise ValueError("timezone was not supplied at process startup")
    method = "startup_environment"
    if hasattr(time, "tzset"):
        time.tzset()
        method = "tzset"
    # Check winter and summer independently against the requested IANA zone.
    # Unsupported Windows IANA contexts fail instead of pretending TZ worked.
    zone = timezone.utc if case.timezone == "UTC" else ZoneInfo(case.timezone)
    for stamp in (1579046400, 1594771200):
        actual = time.localtime(stamp)
        wanted = datetime.fromtimestamp(stamp, zone)
        if actual[:6] != (wanted.year, wanted.month, wanted.day, wanted.hour, wanted.minute, wanted.second):
            raise ValueError("effective timezone could not be verified")
    decimal.getcontext().prec = case.decimal_precision
    decimal.getcontext().rounding = case.decimal_rounding
    if (decimal.getcontext().prec, decimal.getcontext().rounding) != (case.decimal_precision, case.decimal_rounding):
        raise ValueError("effective Decimal context differs")
    return ContextAcknowledgement(case=case, hash_seed_verified=True, timezone_verified=True,
                                  timezone_method=method, decimal_verified=True, target_not_imported=True)


def worker_environment(case: DeterminismCase) -> dict[str, str]:
    # This private launch environment is never an artifact or public diagnostic.
    env = os.environ.copy()
    env.update(PYTHONHASHSEED=str(case.python_hash_seed), TZ=case.timezone,
               POLARS_MAX_THREADS="4", PYTHONUNBUFFERED="1", PYTHONDONTWRITEBYTECODE="1")
    return env
