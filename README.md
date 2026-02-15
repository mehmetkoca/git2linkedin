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

It is optimized for public LinkedIn writing:
- Feature-based output (not repository statistics)
- No commit hashes, file paths, or raw internal commit text in final output
- Emphasis on end-user value and business relevance
- Passive, neutral sentence style (no first-person wording)
- Direct commit-message reading (no theme extraction layer)

## Project Layout

```text
skills/git2linkedin/
  SKILL.md
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
  "summary": "In the role of Software Engineer at Acme, commit-message-driven feature highlights were generated ...",
  "feature_highlights": [
    "Issue resolution was completed in user onboarding flow.",
    "Feature delivery was completed in account recovery experience."
  ],
  "end_user_outcomes": [
    "User-facing disruptions were reduced in critical journeys."
  ],
  "business_relevance": [
    "Core business workflows were protected from avoidable service degradation."
  ],
  "source_mode": "direct-commit-messages"
}
```

## Suggested LinkedIn Formatting

Use:
- `summary` for your first sentence under the role
- First 4-6 `feature_highlights` as bullet points
- Blend `end_user_outcomes` and `business_relevance` into your final bullet language

Keep the final text concise and impact-focused.
