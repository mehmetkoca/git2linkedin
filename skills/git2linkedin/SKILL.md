---
name: git2linkedin
description: Generate English LinkedIn Experience drafts from a repository's git history. Use when asked to write or improve LinkedIn experience text from real commit activity, either for all-time history or a specific date range (`since`/`until` in YYYY-MM-DD), with mandatory role and company context.
---

# Git2LinkedIn

## Overview

Generate a LinkedIn Experience draft from git history with a role-aware summary and impact bullets.

## Workflow

1. Collect required inputs:
- `role` (required)
- `company` (required)

2. Collect optional inputs:
- `repo` (default `.`)
- `since` (`YYYY-MM-DD`)
- `until` (`YYYY-MM-DD`)
- `author` (default: current git user)
- `out` (optional markdown output path)
- `max-commits` (default `400`)

3. Run the extractor:

```bash
# All-time
python3 skills/git2linkedin/scripts/git_history_extract.py \
  --role "Senior Software Engineer" \
  --company "Acme"

# Date range
python3 skills/git2linkedin/scripts/git_history_extract.py \
  --role "Senior Software Engineer" \
  --company "Acme" \
  --since 2025-01-01 \
  --until 2025-12-31
```

4. Convert JSON output into final LinkedIn text:
- Write one short English summary sentence.
- Write 4-6 impact bullets.
- Prefer measurable impact from `stats`, `areas`, and `tech_signals`.

5. Handle empty ranges explicitly:
- If commit list is empty, explain that no commits were found and suggest widening the date range or changing `author`.

## Output Contract

Use these JSON fields:
- `summary`: baseline sentence for LinkedIn experience
- `highlights`: impact-oriented bullet candidates
- `stats`: commit/file/churn metrics
- `areas`: top changed project areas
- `tech_signals`: top technology signals
- `guidance`: fallback suggestion when history is empty

## Guardrails

- Keep output in English unless user asks otherwise.
- Keep bullets concise and outcome-focused.
- Do not invent technologies or impact beyond git evidence.
