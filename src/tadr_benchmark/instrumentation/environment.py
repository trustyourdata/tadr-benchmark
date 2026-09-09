"""Capture only approved fields; never call host, user, network or environment APIs."""

import platform
import re
from importlib.metadata import PackageNotFoundError, version

import psutil

from ..models import EnvironmentInfo

DEPENDENCIES = ("tadr-benchmark", "tadr-core", "pydantic", "polars", "polars-runtime-32", "pyarrow", "psutil",
                "matplotlib", "PyYAML", "numpy", "contourpy", "cycler", "fonttools",
                "kiwisolver", "packaging", "pillow", "pyparsing", "python-dateutil",
                "six", "pydantic-core", "annotated-types", "typing-extensions", "typing-inspection")


def capture_environment() -> EnvironmentInfo:
    versions = {}
    for dependency in DEPENDENCIES:
        try:
            versions[dependency] = version(dependency)
        except PackageNotFoundError:
            continue
    # Release prefixes contain OS versions, unlike platform.version()/uname(),
    # which can expose build hosts and other arbitrary machine-specific text.
    release = re.match(r"\d+(?:\.\d+){0,2}", platform.release())
    system = platform.system()
    machine = platform.machine().lower()
    return EnvironmentInfo(
        os=system if system in {"Windows", "Linux", "Darwin", "FreeBSD"} else "Other",
        os_version=release.group() if release else None,
        architecture=machine if machine in {"amd64", "x86_64", "arm64", "aarch64", "i386", "i686"} else "other",
        python_version=platform.python_version(), cpu_model=None,
        physical_cpu_count=psutil.cpu_count(logical=False),
        logical_cpu_count=psutil.cpu_count(logical=True),
        total_memory_bytes=psutil.virtual_memory().total,
        dependency_versions=versions,
    )
