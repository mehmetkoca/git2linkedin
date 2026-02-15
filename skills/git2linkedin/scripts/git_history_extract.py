#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
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

EXTENSION_TO_TECH = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "React/TypeScript",
    ".jsx": "React/JavaScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".sql": "SQL",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".tf": "Terraform",
    ".dockerfile": "Docker",
}


def fail(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return singular
    return plural if plural else f"{singular}s"


def run_git(repo_path: str, args: list[str], check: bool = True) -> str:
    cmd = ["git", "-C", repo_path, *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
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


def parse_log(raw: str) -> list[dict[str, Any]]:
    commits: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in raw.splitlines():
        if line.startswith("__COMMIT__\x1f"):
            if current is not None:
                commits.append(current)
            parts = line.split("\x1f", 4)
            if len(parts) < 5:
                continue
            current = {
                "hash": parts[1].strip(),
                "date": parts[2].strip(),
                "subject": normalize_space(parts[3]),
                "body": normalize_space(parts[4]),
                "files": [],
                "insertions": 0,
                "deletions": 0,
            }
            continue

        if not line.strip() or current is None:
            continue

        columns = line.split("\t")
        if len(columns) != 3:
            continue

        added_raw, deleted_raw, file_path = columns
        added = int(added_raw) if added_raw.isdigit() else 0
        deleted = int(deleted_raw) if deleted_raw.isdigit() else 0
        current["files"].append(file_path.strip())
        current["insertions"] += added
        current["deletions"] += deleted

    if current is not None:
        commits.append(current)
    return commits


def normalize_space(value: str) -> str:
    return " ".join(value.split())


def is_low_signal_subject(subject: str) -> bool:
    if not subject.strip():
        return True
    return any(pattern.search(subject) for pattern in LOW_SIGNAL_PATTERNS)


def infer_area(file_path: str) -> str:
    normalized = file_path.strip().replace("\\", "/")
    if not normalized:
        return "root"
    if normalized.startswith("{") and "=>" in normalized and "}" in normalized:
        normalized = normalized.split("}", 1)[-1].lstrip("/")
    top = normalized.split("/", 1)[0]
    if top in ("", "."):
        return "root"
    return top


def infer_extension(file_path: str) -> str:
    lowered = file_path.lower()
    if lowered.endswith("dockerfile"):
        return ".dockerfile"
    return Path(lowered).suffix


def build_highlights(
    meaningful_commits: list[dict[str, Any]],
    unique_files: set[str],
    area_counts: Counter[str],
    tech_counts: Counter[str],
    total_insertions: int,
    total_deletions: int,
) -> list[str]:
    if not meaningful_commits:
        return []

    highlights: list[str] = []
    commit_count = len(meaningful_commits)
    area_count = len(area_counts)
    commit_word = pluralize(commit_count, "commit")
    file_word = pluralize(len(unique_files), "file")
    area_word = pluralize(area_count, "area")
    highlights.append(
        f"Shipped {commit_count} meaningful {commit_word} touching {len(unique_files)} {file_word} across {area_count} project {area_word}."
    )

    if total_insertions > 0 or total_deletions > 0:
        insertion_word = pluralize(total_insertions, "insertion")
        deletion_word = pluralize(total_deletions, "deletion")
        highlights.append(
            f"Drove substantial code evolution with about {total_insertions} {insertion_word} and {total_deletions} {deletion_word}."
        )

    if area_counts:
        top_area, top_area_changes = area_counts.most_common(1)[0]
        change_word = pluralize(top_area_changes, "change")
        highlights.append(
            f"Focused strongly on {top_area}, contributing {top_area_changes} file-level {change_word} in that area."
        )

    if tech_counts:
        top_techs = [f"{tech} ({count})" for tech, count in tech_counts.most_common(3)]
        highlights.append(
            f"Worked across a broad stack with visible activity in {', '.join(top_techs)}."
        )

    recent_subjects = []
    for commit in meaningful_commits:
        subject = commit["subject"].strip()
        if subject and subject not in recent_subjects:
            recent_subjects.append(subject)
        if len(recent_subjects) == 3:
            break

    for subject in recent_subjects:
        if len(highlights) >= 6:
            break
        highlights.append(f"Delivered changes such as: {subject}.")

    while len(highlights) < 4 and recent_subjects:
        idx = len(highlights) % len(recent_subjects)
        highlights.append(f"Delivered iterative improvements, including: {recent_subjects[idx]}.")

    return highlights[:6]


def build_summary(
    role: str,
    company: str,
    time_label: str,
    meaningful_count: int,
    unique_file_count: int,
    area_counts: Counter[str],
    tech_counts: Counter[str],
) -> str:
    if meaningful_count == 0:
        return (
            f"As {role} at {company}, no meaningful commits were detected {time_label}; "
            "widen the time range or adjust the author filter."
        )

    top_area = area_counts.most_common(1)[0][0] if area_counts else "core project areas"
    top_tech = tech_counts.most_common(1)[0][0] if tech_counts else "multiple technologies"
    commit_word = pluralize(meaningful_count, "commit")
    file_word = pluralize(unique_file_count, "file")
    return (
        f"As {role} at {company}, shipped {meaningful_count} meaningful {commit_word} {time_label}, "
        f"touching {unique_file_count} {file_word} with notable focus on {top_area} and {top_tech}."
    )


def write_markdown_output(path: str, data: dict[str, Any]) -> None:
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# LinkedIn Experience Draft",
        "",
        f"- Role: {data['role']}",
        f"- Company: {data['company']}",
        f"- Author filter: {data['author']}",
        f"- Time mode: {data['time_range']['mode']}",
        "",
        "## Summary",
        "",
        data["summary"],
        "",
        "## Highlights",
        "",
    ]

    highlights = data.get("highlights", [])
    if highlights:
        lines.extend([f"- {item}" for item in highlights])
    else:
        lines.append("- No meaningful commit highlights were detected.")

    guidance = data.get("guidance")
    if guidance:
        lines.extend(["", "## Guidance", "", guidance])

    output_path.write_text("\n".join(lines) + "\n")


def build_time_label(since: str | None, until: str | None) -> str:
    if not since and not until:
        return "across the repository's full history"
    if since and until:
        return f"between {since} and {until}"
    if since:
        return f"from {since} onward"
    return f"up to {until}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract git history signals for LinkedIn Experience drafting."
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
        "--numstat",
        f"--max-count={args.max_commits}",
        f"--author={author}",
        "--pretty=format:__COMMIT__%x1f%H%x1f%ad%x1f%s%x1f%b",
    ]
    if args.since:
        log_args.append(f"--since={args.since}")
    if args.until:
        log_args.append(f"--until={args.until}")

    raw_log = run_git(repo_path, log_args)
    commits = parse_log(raw_log)
    meaningful_commits = [c for c in commits if not is_low_signal_subject(c["subject"])]

    unique_files: set[str] = set()
    area_counts: Counter[str] = Counter()
    tech_counts: Counter[str] = Counter()
    total_insertions = 0
    total_deletions = 0

    for commit in meaningful_commits:
        total_insertions += commit["insertions"]
        total_deletions += commit["deletions"]
        for file_path in commit["files"]:
            unique_files.add(file_path)
            area_counts[infer_area(file_path)] += 1
            ext = infer_extension(file_path)
            tech = EXTENSION_TO_TECH.get(ext)
            if tech:
                tech_counts[tech] += 1

    time_mode = "all-time" if not args.since and not args.until else "bounded"
    time_label = build_time_label(args.since, args.until)
    summary = build_summary(
        role=args.role,
        company=args.company,
        time_label=time_label,
        meaningful_count=len(meaningful_commits),
        unique_file_count=len(unique_files),
        area_counts=area_counts,
        tech_counts=tech_counts,
    )
    highlights = build_highlights(
        meaningful_commits=meaningful_commits,
        unique_files=unique_files,
        area_counts=area_counts,
        tech_counts=tech_counts,
        total_insertions=total_insertions,
        total_deletions=total_deletions,
    )

    guidance = None
    if not commits:
        guidance = "No commits found in this range. Widen the date range or verify the author filter."
    elif not meaningful_commits:
        guidance = (
            "Commits were found but all were filtered as low-signal. "
            "Adjust commit naming or lower filtering strictness."
        )

    result = {
        "repo": repo_path,
        "role": args.role,
        "company": args.company,
        "author": author,
        "time_range": {
            "mode": time_mode,
            "since": args.since,
            "until": args.until,
        },
        "filters": {
            "max_commits": args.max_commits,
            "low_signal_filter": True,
            "low_signal_patterns": [
                "chore",
                "wip",
                "bump",
                "release",
                "typo",
                "format",
                "lint",
                "docs",
            ],
        },
        "stats": {
            "raw_commits": len(commits),
            "meaningful_commits": len(meaningful_commits),
            "unique_files_touched": len(unique_files),
            "areas_touched": len(area_counts),
            "insertions": total_insertions,
            "deletions": total_deletions,
        },
        "areas": [
            {"name": name, "changes": count}
            for name, count in area_counts.most_common(10)
        ],
        "tech_signals": [
            {"name": name, "changes": count}
            for name, count in tech_counts.most_common(10)
        ],
        "recent_meaningful_commits": [
            {
                "hash": commit["hash"][:7],
                "date": commit["date"],
                "subject": commit["subject"],
            }
            for commit in meaningful_commits[:10]
        ],
        "summary": summary,
        "highlights": highlights,
        "guidance": guidance,
    }

    if args.out:
        write_markdown_output(args.out, result)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
