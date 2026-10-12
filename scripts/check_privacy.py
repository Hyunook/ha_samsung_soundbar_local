#!/usr/bin/env python3
"""Block personal or secret data before it enters the integration repository."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

SELF = Path(__file__).resolve()
MAX_TEXT_SIZE = 2 * 1024 * 1024
TEXT_SUFFIXES = {
    ".cfg",
    ".conf",
    ".env",
    ".http",
    ".ini",
    ".json",
    ".md",
    ".properties",
    ".py",
    ".toml",
    ".txt",
    ".svg",
    ".xml",
    ".yaml",
    ".yml",
}
SENSITIVE_SUFFIXES = {
    ".apk",
    ".bak",
    ".backup",
    ".crt",
    ".csv",
    ".db",
    ".der",
    ".doc",
    ".docx",
    ".gif",
    ".gz",
    ".har",
    ".heic",
    ".jpg",
    ".jpeg",
    ".key",
    ".log",
    ".old",
    ".p12",
    ".pcap",
    ".pcapng",
    ".pdf",
    ".pem",
    ".pfx",
    ".png",
    ".sqlite",
    ".sqlite3",
    ".tar",
    ".tgz",
    ".webp",
    ".xls",
    ".xlsx",
    ".xz",
    ".zip",
}
SENSITIVE_FILENAMES = {
    ".env",
    "auth_providers.yaml",
    "configuration.yaml",
    "secrets.yaml",
}
SENSITIVE_DIRECTORY_PARTS = {
    ".storage",
    "backups",
    "captures",
    "credentials",
    "diagnostics",
    "exports",
    "secrets",
}
ALLOWED_ALLOWLIST_NAMES = {
    ".env.example",
    ".env.sample",
    ".env.template",
}
# Brand images are loaded from Home Assistant Brands, never committed.
ALLOWED_REPOSITORY_IMAGES: set[str] = set()
ALLOWED_HOSTS = {"0.0.0.0", "127.0.0.1", "::1", "localhost"}
PLACEHOLDER_MARKERS = {
    "changeme",
    "dummy",
    "example",
    "invalid",
    "placeholder",
    "replace-me",
    "test-token",
    "your-token",
}

PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
JWT_RE = re.compile(
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
)
BEARER_RE = re.compile(r"(?i)\bBearer\s+(?!<|\{|\$|os\.)[A-Za-z0-9._~+/-]{12,}={0,2}")
TOKEN_RE = re.compile(
    r"\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})\b"
)
UUID_RE = re.compile(
    r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}\b"
)
MAC_RE = re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b")
IPV4_RE = re.compile(r"(?<![\d.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![\d.])")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
WINDOWS_USER_PATH_RE = re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+")
CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"""(?ix)\b(api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token|
    password|passwd|secret|token)\b\s*[:=]\s*["']([^"'\r\n]{6,})["']"""
)
PII_ASSIGNMENT_RE = re.compile(
    r"""(?ix)\b(ssid|serial(?:number)?|device[_-]?id|username|email|phone|
    hostname|host|ip)\b\s*[:=]\s*["']([^"'\r\n]{2,})["']"""
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str
    detail: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.kind}: {self.detail}"


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def nul_paths(data: bytes) -> list[str]:
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in data.split(b"\0")
        if item
    ]


def candidate_paths(root: Path) -> list[str]:
    result = run_git(
        root, "ls-files", "--cached", "--others", "--exclude-standard", "-z"
    )
    if result.returncode == 0:
        return sorted(set(nul_paths(result.stdout)))
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )


def staged_paths(root: Path) -> set[str]:
    if not (root / ".git").exists():
        return set()
    head = run_git(root, "rev-parse", "--verify", "HEAD")
    args = (
        ("ls-files", "--cached", "-z")
        if head.returncode
        else (
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMR",
            "-z",
        )
    )
    result = run_git(root, *args)
    return set(nul_paths(result.stdout)) if result.returncode == 0 else set()


def read_candidate(root: Path, relative: str, use_index: bool) -> bytes | None:
    if use_index:
        result = run_git(root, "show", f":{relative}")
        if result.returncode == 0:
            return result.stdout
    path = root / Path(relative)
    try:
        return path.read_bytes()
    except OSError:
        return None


def is_placeholder(value: str) -> bool:
    normalized = value.strip().strip("\"'").lower()
    if not normalized or normalized in ALLOWED_HOSTS:
        return True
    if normalized.startswith("<") and normalized.endswith(">"):
        return True
    if any(marker in normalized for marker in PLACEHOLDER_MARKERS):
        return True
    if normalized in {"none", "null", "false", "true", "test", "unknown"}:
        return True
    return normalized.count("x") >= 4 or normalized.count("*") >= 4


def redact(value: str) -> str:
    compact = value.strip()
    if len(compact) <= 8:
        return "<found>"
    return f"{compact[:3]}…{compact[-2:]} ({len(compact)} characters)"


def valid_ipv4(value: str) -> bool:
    parts = value.split(".")
    return len(parts) == 4 and all(
        part.isdigit() and 0 <= int(part) <= 255 for part in parts
    )


def filename_findings(relative: str) -> list[Finding]:
    lowered = relative.lower()
    path = PurePosixPath(lowered)
    name = path.name
    findings: list[Finding] = []

    if name in ALLOWED_ALLOWLIST_NAMES or lowered in ALLOWED_REPOSITORY_IMAGES:
        return findings
    if name in SENSITIVE_FILENAMES or path.suffix in SENSITIVE_SUFFIXES:
        findings.append(Finding(relative, 0, "sensitive file", "must not be committed"))
    if name == ".env" or (
        name.startswith(".env.") and name not in ALLOWED_ALLOWLIST_NAMES
    ):
        findings.append(
            Finding(relative, 0, "environment file", "must not be committed")
        )
    for part in path.parts[:-1]:
        if part in SENSITIVE_DIRECTORY_PARTS:
            findings.append(
                Finding(relative, 0, "sensitive directory", "must not be committed")
            )
            break
    return findings


def text_findings(relative: str, content: bytes) -> list[Finding]:
    if b"\0" in content:
        return []
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content.decode("cp1252")
        except UnicodeDecodeError:
            return []

    findings: list[Finding] = []
    if len(content) > MAX_TEXT_SIZE:
        findings.append(
            Finding(
                relative, 0, "large text file", f"{len(content)} bytes; review manually"
            )
        )

    for line_number, line in enumerate(text.splitlines(), start=1):
        checks = (
            ("private key", PRIVATE_KEY_RE.search(line)),
            ("JWT", JWT_RE.search(line)),
            ("bearer token", BEARER_RE.search(line)),
            ("API/Git token", TOKEN_RE.search(line)),
            ("UUID", UUID_RE.search(line)),
            ("MAC address", MAC_RE.search(line)),
            ("email address", EMAIL_RE.search(line)),
            ("Windows user path", WINDOWS_USER_PATH_RE.search(line)),
        )
        for kind, match in checks:
            if not match:
                continue
            value = match.group(0)
            if kind == "email address" and (
                is_placeholder(value)
                or re.search(r"https?://[^\s\"']*$", line[: match.start()])
            ):
                continue
            if kind in {"UUID", "MAC address"} and is_placeholder(value):
                continue
            findings.append(Finding(relative, line_number, kind, redact(value)))

        for match in IPV4_RE.finditer(line):
            value = match.group(0)
            if valid_ipv4(value) and not is_placeholder(value):
                findings.append(
                    Finding(relative, line_number, "IP address", redact(value))
                )

        for match in CREDENTIAL_ASSIGNMENT_RE.finditer(line):
            value = match.group(2)
            if not is_placeholder(value):
                findings.append(
                    Finding(relative, line_number, "credential", redact(value))
                )

        for match in PII_ASSIGNMENT_RE.finditer(line):
            value = match.group(2)
            if not is_placeholder(value):
                findings.append(
                    Finding(relative, line_number, "personal field", redact(value))
                )

    return findings


def scan(root: Path) -> list[Finding]:
    root = root.resolve()
    staged = staged_paths(root)
    findings: list[Finding] = []
    for relative in candidate_paths(root):
        if Path(relative).resolve() == SELF:
            continue
        findings.extend(filename_findings(relative))
        content = read_candidate(root, relative, relative in staged)
        if content is not None:
            findings.extend(text_findings(relative, content))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=SELF.parents[1],
        help="Repository root; defaults to the parent directory of scripts/.",
    )
    args = parser.parse_args()

    findings = scan(args.root)
    if findings:
        print("BLOCKED: Potential personal data or secrets detected.", file=sys.stderr)
        for finding in findings:
            print(f"- {finding.render()}", file=sys.stderr)
        print(
            "\nNo commit created. Remove the values or replace them with synthetic placeholders.",
            file=sys.stderr,
        )
        return 1

    print("Privacy check passed: no personal data or secrets detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
