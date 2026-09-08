"""Conservative public-text checks; diagnostics never echo matched content."""

import re
import json
import subprocess
from pathlib import Path

# Patterns are detectors, never examples containing real private values.
RULES = {
    "absolute-windows-path": re.compile(r"(?i)\b[a-z]:[\\/]"),
    "private-unix-path": re.compile(r"/(?:home|Users|private|tmp|var|mnt|opt|workspace|workspaces)/[^\s\"']+"),
    "network-path": re.compile(r"\\\\[A-Za-z0-9_.-]+\\"),
    "ipv4-address": re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])"),
    "mac-address": re.compile(r"(?i)(?<![\w])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![\w])"),
    "ipv6-address": re.compile(r"(?i)(?:\b[0-9a-f]{1,4}:){3,}[0-9a-f:]+|\[::[0-9a-f:]+\]"),
    "machine-identifier": re.compile(r"(?i)\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b"),
    "credential-url": re.compile(r"(?i)https?://[^\s/@]+:[^\s/@]+@"),
    "private-key": re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"),
    "access-token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{20,})\b"),
    "assigned-secret": re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|password|client[_-]?secret)\s*[=:]\s*[\"']?[A-Za-z0-9_+/=-]{12,}"),
    "private-strategy": re.compile(r"(?i)\b(?:N" + r"IW|immigration\s+strategy|petition\s+strategy|customer\s+pipeline|fundraising\s+strategy)\b"),
    "raw-traceback": re.compile(r"Traceback \(most recent call last\)"),
}


def text_issues(text: str) -> list[str]:
    return sorted(name for name, pattern in RULES.items() if pattern.search(text))


def structured_issues(value) -> list[str]:
    """Public JSON has typed observations, never process/environment dumps."""
    forbidden = {"pid", "ppid", "pids", "process_id", "process_ids", "command_line", "commandline", "cmdline", "argv",
                 "hostname", "host_name", "username", "user_name", "environment_dump", "environ", "env",
                 "traceback", "stacktrace", "exception_message", "error_message", "raw_exception",
                 "stdout", "stderr", "cwd", "home_directory", "local_checkout", "checkout_path", "installation_artifact", "target_artifact_path", "target_git_commit"}
    issues = set()
    def visit(node):
        if isinstance(node, dict):
            for key, child in node.items():
                if key.lower() in forbidden:
                    issues.add("forbidden-public-diagnostic-field")
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)
    visit(value)
    return sorted(issues)


def scan_files(root: Path, paths: list[str]) -> list[str]:
    from .paths import contained, safe_relative
    issues = []
    forbidden_parts = {".work", ".venv", ".codex", ".agents", "__pycache__", "paper"}
    forbidden_suffixes = {".pem", ".key", ".p12", ".pfx", ".log", ".prof", ".trace"}
    for relative in sorted(set(paths)):
        try:
            parts = safe_relative(relative).parts
            path = contained(root, relative)
        except ValueError:
            issues.append("unsafe repository path")
            continue
        # Do not follow symlinks, including intermediate directory links.
        if any(root.joinpath(*parts[:index]).is_symlink() for index in range(1, len(parts) + 1)):
            issues.append(f"{relative}: symlink artifact")
            continue
        if (set(parts) & forbidden_parts or path.name.startswith((".env", "benchmark.local.", "local_config."))
                or path.suffix.lower() in forbidden_suffixes
                or any(word in path.name.lower() for word in ("pasted-text", "review-artifact", "implementation-prompt", "design_proposal"))):
            issues.append(f"{relative}: prohibited artifact")
        if not path.is_file():
            continue
        data = path.read_bytes()
        try:
            content = data.decode("utf-8-sig")
            if "\x00" in content:
                raise UnicodeError("binary")
        except UnicodeError:
            # Images need visual review; datasets are not public by default.
            if not (parts[:2] == ("results", "campaigns") and path.suffix in {".png", ".pdf"}):
                issues.append(f"{relative}: unreviewable binary artifact")
            continue
        for issue in text_issues(relative + "\n" + content):
            issues.append(f"{relative}: {issue}")
        if path.suffix in {".json", ".jsonl"}:
            try:
                values = [json.loads(line) for line in content.splitlines() if line.strip()] if path.suffix == ".jsonl" else [json.loads(content)]
                for issue in sorted({issue for value in values for issue in structured_issues(value)}):
                    issues.append(f"{relative}: {issue}")
            except ValueError:
                issues.append(f"{relative}: invalid public JSON")
    return issues


def repository_issues(root: Path, include_untracked: bool = False) -> list[str]:
    args = ["git", "ls-files", "-z", "--cached"]
    if include_untracked:
        args.extend(["--others", "--exclude-standard"])
    output = subprocess.run(args, cwd=root, check=True, capture_output=True).stdout
    return scan_files(root, [item.decode("utf-8") for item in output.split(b"\0") if item])
