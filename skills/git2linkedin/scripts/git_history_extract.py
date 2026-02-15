#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

LOW_SIGNAL_PATTERNS = [
    re.compile(r"^(chore)(\(|:|\b)", re.IGNORECASE),
    re.compile(r"^(wip)(\(|:|\b)", re.IGNORECASE),
    re.compile(r"^(bump)(\(|:|\b)", re.IGNORECASE),
    re.compile(r"^(release)(\(|:|\b)", re.IGNORECASE),
    re.compile(r"^(typo)(\(|:|\b)", re.IGNORECASE),
    re.compile(r"^(format)(\(|:|\b)", re.IGNORECASE),
    re.compile(r"^(lint)(\(|:|\b)", re.IGNORECASE),
    re.compile(r"^(docs?)(\(|:|\b)", re.IGNORECASE),
]

SENSITIVE_PATTERNS = [
    re.compile(r"https?://\S+", re.IGNORECASE),
    re.compile(r"\b[A-Z]{2,10}-\d+\b"),
    re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE),
    re.compile(r"\b\S+@\S+\b"),
]

ACTION_VERBS = {
    "add",
    "added",
    "build",
    "built",
    "create",
    "created",
    "deliver",
    "delivered",
    "implement",
    "implemented",
    "introduce",
    "introduced",
    "improve",
    "improved",
    "enhance",
    "enhanced",
    "optimize",
    "optimized",
    "fix",
    "fixed",
    "resolve",
    "resolved",
    "repair",
    "repaired",
    "refactor",
    "refactored",
    "update",
    "updated",
    "reduce",
    "reduced",
    "increase",
    "increased",
}

STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "for",
    "to",
    "of",
    "in",
    "on",
    "with",
    "by",
    "from",
    "at",
    "into",
    "across",
    "over",
    "flow",
    "flows",
    "feature",
    "features",
    "issue",
    "issues",
}


def fail(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def run_git(repo_path: str, args: list[str]) -> str:
    cmd = ["git", "-C", repo_path, *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"Git command failed: {' '.join(cmd)}\n{result.stderr.strip()}")
    return result.stdout


def validate_date(value: str, field: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        fail(f"Invalid {field} date '{value}'. Expected format: YYYY-MM-DD")


def resolve_repo_path(repo: str) -> str:
    path = Path(repo).expanduser().resolve()
    if not path.exists():
        fail(f"Repository path does not exist: {path}")

    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or result.stdout.strip() != "true":
        fail(f"Not a git repository: {path}")
    return str(path)


def detect_current_git_user(repo_path: str) -> str:
    for key in ("user.name", "user.email"):
        result = subprocess.run(
            ["git", "-C", repo_path, "config", "--get", key],
            capture_output=True,
            text=True,
        )
        value = result.stdout.strip()
        if result.returncode == 0 and value:
            return value
    fail("Could not detect current git user. Provide --author explicitly.")


def normalize_space(value: str) -> str:
    return " ".join(value.split())


def scrub_sensitive_text(value: str) -> str:
    text = normalize_space(value)
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub("", text)
    return normalize_space(text)


def is_low_signal_subject(subject: str) -> bool:
    if not subject.strip():
        return True
    return any(pattern.search(subject) for pattern in LOW_SIGNAL_PATTERNS)


def strip_conventional_prefix(subject: str) -> str:
    return re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?:\s*", "", subject.strip())


def parse_log(raw: str) -> list[dict[str, str]]:
    matches = re.finditer(
        r"__COMMIT__\x1f([^\x1f]*)\x1f([^\x1f]*)\x1f(.*?)(?=\n__COMMIT__\x1f|\Z)",
        raw,
        re.DOTALL,
    )
    commits: list[dict[str, str]] = []
    for match in matches:
        date = match.group(1).strip()
        subject = scrub_sensitive_text(match.group(2))
        body = scrub_sensitive_text(match.group(3))
        commits.append({"date": date, "subject": subject, "body": body})
    return commits


def classify_action(subject: str) -> str:
    lowered = subject.lower()
    if any(word in lowered for word in ("fix", "resolve", "repair", "bug", "hotfix")):
        return "issue-resolution"
    if any(word in lowered for word in ("optimiz", "perf", "latency", "speed", "cache")):
        return "performance"
    if any(word in lowered for word in ("secure", "security", "privacy", "permission", "access")):
        return "security"
    if any(word in lowered for word in ("integrat", "api", "webhook", "sync", "export", "import")):
        return "integration"
    if any(word in lowered for word in ("refactor", "cleanup", "simplify", "maintain")):
        return "maintainability"
    return "feature-delivery"


def extract_safe_focus(subject: str) -> str:
    base = strip_conventional_prefix(subject)
    base = re.sub(r"[^\w\s-]", " ", base)
    tokens = base.lower().split()
    safe_tokens = []
    for token in tokens:
        if token in ACTION_VERBS or token in STOP_WORDS:
            continue
        if not re.match(r"^[a-z]+$", token):
            continue
        if len(token) < 3:
            continue
        safe_tokens.append(token)
        if len(safe_tokens) == 4:
            break
    return " ".join(safe_tokens)


def build_passive_line(action: str, focus: str) -> str:
    focus_suffix = f" in {focus}" if focus else ""
    if action == "issue-resolution":
        return f"Issue resolution was completed{focus_suffix}."
    if action == "performance":
        return f"Performance optimization was completed{focus_suffix}."
    if action == "security":
        return f"Security and privacy hardening was completed{focus_suffix}."
    if action == "integration":
        return f"Integration enablement was completed{focus_suffix}."
    if action == "maintainability":
        return f"Maintainability improvements were completed{focus_suffix}."
    return f"Feature delivery was completed{focus_suffix}."


def unique_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def build_time_label(since: str | None, until: str | None) -> str:
    if not since and not until:
        return "across the full period"
    if since and until:
        return f"between {since} and {until}"
    if since:
        return f"from {since} onward"
    return f"up to {until}"


def build_summary(role: str, company: str, time_label: str) -> str:
    return (
        f"In the role of {role} at {company}, commit-message-driven feature highlights were generated "
        f"{time_label} with confidentiality-safe language for LinkedIn."
    )


def build_feature_highlights(commits: list[dict[str, str]]) -> list[str]:
    lines = []
    for commit in commits:
        action = classify_action(commit["subject"])
        focus = extract_safe_focus(commit["subject"])
        lines.append(build_passive_line(action, focus))
        if len(lines) == 6:
            break
    if not lines:
        lines = [
            "Feature delivery was completed in customer-facing workflows.",
            "Execution was aligned with business-critical workflows.",
            "User-facing experience quality was improved in core journeys.",
            "Production-readiness expectations were met in delivered work.",
        ]
    return unique_preserve_order(lines)[:6]


def build_end_user_outcomes(commits: list[dict[str, str]]) -> list[str]:
    actions = [classify_action(c["subject"]) for c in commits[:12]]
    lines = []
    if "issue-resolution" in actions:
        lines.append("User-facing disruptions were reduced in critical journeys.")
    if "performance" in actions:
        lines.append("Waiting time was reduced in key user interactions.")
    if "security" in actions:
        lines.append("User trust was reinforced through stronger protection behaviors.")
    if "integration" in actions:
        lines.append("Cross-workflow usability was improved in connected user journeys.")
    lines.extend(
        [
            "Everyday usability was improved in core user flows.",
            "Consistency was increased in customer-facing product behavior.",
        ]
    )
    return unique_preserve_order(lines)[:4]


def build_business_relevance(commits: list[dict[str, str]]) -> list[str]:
    actions = [classify_action(c["subject"]) for c in commits[:12]]
    lines = []
    if "issue-resolution" in actions:
        lines.append("Core business workflows were protected from avoidable service degradation.")
    if "performance" in actions:
        lines.append("Scalability readiness was improved in peak usage paths.")
    if "security" in actions:
        lines.append("Compliance and reputational risk were reduced in sensitive workflows.")
    if "integration" in actions:
        lines.append("Integration readiness was improved for partner-facing use cases.")
    lines.extend(
        [
            "Execution was aligned with business-critical workflows.",
            "Delivery quality was improved for customer-impacting priorities.",
        ]
    )
    return unique_preserve_order(lines)[:4]


def write_markdown_output(path: str, data: dict[str, Any]) -> None:
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# LinkedIn Experience Draft",
        "",
        f"- Role: {data['role']}",
        f"- Company: {data['company']}",
        f"- Time mode: {data['time_range']['mode']}",
        "",
        "## Summary",
        "",
        data["summary"],
        "",
        "## Feature Highlights",
        "",
    ]
    lines.extend([f"- {item}" for item in data["feature_highlights"]])

    lines.extend(["", "## End-User Outcomes", ""])
    lines.extend([f"- {item}" for item in data["end_user_outcomes"]])

    lines.extend(["", "## Business Relevance", ""])
    lines.extend([f"- {item}" for item in data["business_relevance"]])

    if data.get("guidance"):
        lines.extend(["", "## Guidance", "", data["guidance"]])

    output_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract feature-oriented and confidentiality-safe LinkedIn experience content "
            "directly from commit messages."
        )
    )
    parser.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    parser.add_argument("--role", required=True, help="LinkedIn role title")
    parser.add_argument("--company", required=True, help="LinkedIn company name")
    parser.add_argument("--since", help="Start date in YYYY-MM-DD")
    parser.add_argument("--until", help="End date in YYYY-MM-DD")
    parser.add_argument("--author", help="Git author filter; defaults to current git user")
    parser.add_argument("--out", help="Optional markdown output file path")
    parser.add_argument(
        "--max-commits",
        type=int,
        default=400,
        help="Maximum commits to inspect (default: 400)",
    )
    args = parser.parse_args()

    if args.max_commits <= 0:
        fail("--max-commits must be greater than 0")

    if args.since:
        validate_date(args.since, "since")
    if args.until:
        validate_date(args.until, "until")
    if args.since and args.until and args.since > args.until:
        fail(f"Invalid range: since ({args.since}) is after until ({args.until})")

    repo_path = resolve_repo_path(args.repo)
    author = args.author or detect_current_git_user(repo_path)

    log_args = [
        "log",
        "--no-merges",
        "--date=short",
        f"--max-count={args.max_commits}",
        f"--author={author}",
        "--pretty=format:__COMMIT__%x1f%ad%x1f%s%x1f%b",
    ]
    if args.since:
        log_args.append(f"--since={args.since}")
    if args.until:
        log_args.append(f"--until={args.until}")

    raw_log = run_git(repo_path, log_args)
    commits = parse_log(raw_log)
    meaningful_commits = [c for c in commits if not is_low_signal_subject(c["subject"])]

    time_mode = "all-time" if not args.since and not args.until else "bounded"
    time_label = build_time_label(args.since, args.until)
    summary = build_summary(args.role, args.company, time_label)

    feature_highlights = build_feature_highlights(meaningful_commits)
    end_user_outcomes = build_end_user_outcomes(meaningful_commits)
    business_relevance = build_business_relevance(meaningful_commits)

    guidance = None
    if not commits:
        guidance = "No commits found in this range. Widen the date range or verify the author filter."
    elif not meaningful_commits:
        guidance = (
            "Commits were found but they were too low-signal for feature extraction. "
            "Try a different date range or review commit message quality."
        )

    result = {
        "role": args.role,
        "company": args.company,
        "time_range": {
            "mode": time_mode,
            "since": args.since,
            "until": args.until,
        },
        "summary": summary,
        "feature_highlights": feature_highlights,
        "end_user_outcomes": end_user_outcomes,
        "business_relevance": business_relevance,
        "source_mode": "direct-commit-messages",
        "confidentiality": {
            "includes_repository_statistics": False,
            "includes_commit_hashes_or_file_paths": False,
            "includes_raw_commit_messages": False,
        },
        "guidance": guidance,
    }

    if args.out:
        write_markdown_output(args.out, result)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
