# Git2LinkedIn

Turn commit history into career storytelling: generate polished English LinkedIn Experience drafts from your git log, for all time or any date range.

## What It Does

`git2linkedin` analyzes meaningful commits and produces structured JSON you can turn into:
- One short experience summary
- 4-6 impact bullets

It supports:
- All-time mode (default)
- Date-bounded mode (`--since`, `--until`)
- Author filtering (defaults to current git user)
- Optional markdown draft export (`--out`)

## Project Layout

```text
skills/git2linkedin/
  SKILL.md
  agents/openai.yaml
  scripts/git_history_extract.py
```

## Quick Start

Requirements:
- `git`
- `python3`

Run in all-time mode:

```bash
python3 skills/git2linkedin/scripts/git_history_extract.py \
  --role "Senior Software Engineer" \
  --company "Acme"
```

Run with a date range:

```bash
python3 skills/git2linkedin/scripts/git_history_extract.py \
  --role "Senior Software Engineer" \
  --company "Acme" \
  --since 2025-01-01 \
  --until 2025-12-31
```

Write a markdown draft as well:

```bash
python3 skills/git2linkedin/scripts/git_history_extract.py \
  --role "Senior Software Engineer" \
  --company "Acme" \
  --out /tmp/linkedin-experience.md
```

## CLI Arguments

- `--repo`: repository path (default: `.`)
- `--role`: LinkedIn role title (required)
- `--company`: LinkedIn company name (required)
- `--since`: start date in `YYYY-MM-DD`
- `--until`: end date in `YYYY-MM-DD`
- `--author`: git author filter (default: current git user)
- `--out`: optional markdown output path
- `--max-commits`: maximum commits to inspect (default: `400`)

## Example JSON Output (Truncated)

```json
{
  "role": "Software Engineer",
  "company": "Acme",
  "time_range": {
    "mode": "bounded",
    "since": "2025-06-01",
    "until": "2025-12-31"
  },
  "stats": {
    "raw_commits": 24,
    "meaningful_commits": 13
  },
  "summary": "As Software Engineer at Acme, shipped 13 meaningful commits ...",
  "highlights": [
    "Shipped 13 meaningful commits touching 41 files across 5 project areas.",
    "Worked across a broad stack with visible activity in TypeScript (12), SQL (4)."
  ]
}
```

## Suggested LinkedIn Formatting

Use:
- `summary` for your first sentence under the role
- First 4-6 `highlights` as bullet points

Keep the final text concise and impact-focused.
