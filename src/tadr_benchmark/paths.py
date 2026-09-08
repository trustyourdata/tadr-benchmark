"""Repository-relative paths and containment checks."""

from pathlib import Path, PurePosixPath

from pydantic import TypeAdapter

from .models import Identifier


def safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or "\\" in value or ":" in value
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ValueError("expected a normalized repository-relative path")
    return path


def contained(root: Path, relative: str) -> Path:
    result = root.joinpath(*safe_relative(relative).parts).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError("path escapes repository")
    return result


def campaign_directory(root: Path, campaign_id: str) -> Path:
    TypeAdapter(Identifier).validate_python(campaign_id, strict=True)
    return contained(root, f"results/campaigns/{campaign_id.lower()}")
