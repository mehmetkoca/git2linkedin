# Git2LinkedIn

Turn commit history into career storytelling: generate polished LinkedIn Experience drafts from your git log, for all time or any date range.

## What It Does

`git2linkedin` turns git history into a draft LinkedIn Experience entry.

You provide role and company context, optionally limit the date range, and the skill generates:
- A short summary
- Experience bullets suitable for LinkedIn

The output is designed for public profile use and avoids exposing raw repository internals.

## Install as a Skill

```text
npx skills add https://github.com/mehmetkoca/git2linkedin --skill git2linkedin
```

## Use the Skill

Use natural language in Codex/ChatGPT. Provide your role and company, then ask for a LinkedIn Experience draft.

Example prompts:

- `Use git2linkedin and draft a LinkedIn Experience entry from this repository for role "Senior Software Engineer" at "Acme".`
- `Use git2linkedin for 2025-01-01 to 2025-12-31 and generate a LinkedIn Experience draft.`
- `Use git2linkedin and return one short summary plus 4-6 experience bullets.`

## Suggested LinkedIn Formatting

Use:
- `summary` for your first sentence under the role
- First 4-6 `feature_highlights` as bullet points
- Blend `end_user_outcomes` and `business_relevance` into your final bullet language

Keep the final text concise and impact-focused.
