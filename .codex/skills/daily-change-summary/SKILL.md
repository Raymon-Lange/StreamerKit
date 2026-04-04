---
name: daily-change-summary
description: Summarize repository changes made today with direct updates. Use when the user asks for "summary of changes today", "today's updates", "direct updates", "what changed today", "daily changelog", or similar same-day progress recap requests.
---

# Daily Change Summary

Produce a same-day progress summary from git history and current working tree.

## Workflow

1. Detect today's date in local timezone.
2. Collect committed changes made today.
3. Collect uncommitted changes still in the working tree.
4. Return a direct, concise update grouped by:
- Committed today
- In progress (not committed)
- Risks or follow-ups

## Commands

Use these commands (or equivalents) in this order:

```bash
git log --since="today 00:00" --pretty=format:"%h%x09%ad%x09%s" --date=iso-local
git show --name-only --pretty="" <commit_sha>
git status --short
git diff --name-only
```

If there are no commits today, state that explicitly and still include current working-tree updates.

## Output Rules

- Keep the summary direct and action-oriented.
- Mention concrete files changed and what changed in each.
- Prefer bullets with one-line impact statements.
- Do not include motivational language or filler.
- If nothing changed today, state: `No repository changes detected today.`
