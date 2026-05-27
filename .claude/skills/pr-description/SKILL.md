---
name: pr-description
description: Generate a concise PR description from the current branch diff. Outputs a filled-in template ready to paste into GitHub.
version: 1.0.0
---

# PR Description

Generate a concise PR description for the current branch.

## Steps

1. Run `git log main...HEAD --oneline` to see all commits.
2. Run `git diff main...HEAD --stat` to see files changed and line counts.
3. Run `git diff main...HEAD` to read the full diff.
4. Fill in the template below.

## Rules

- **What does it do?** — 2–4 bullet points max. Each bullet is one sentence. Describe behaviour change, not implementation. Start each bullet with an imperative verb (Add, Fix, Expose, Remove).
- **What else do you need to know?** — only fill if there is a non-obvious constraint, migration step, or breaking change. Leave blank otherwise.
- **Checklist** — pre-tick only what is verifiably true from the diff (tests exist, no new env vars, etc.). Leave the rest unchecked.
- Never mention file names, function names, or commit hashes in the description body.
- Never use "this PR", "this change", or "I". Write in third person imperative.
- Always use `sova-claw` GitHub account when creating the PR (`gh auth switch --user sova-claw` first).

## Output

Print the filled template as a markdown code block, ready to paste.

```
### What does it do?

- <bullet>
- <bullet>

### What else do you need to know?

<content or leave blank>

### Checklist
- [ ] Base branch is set to `main`
- [ ] Pull request is prepared: assignee added, linked to issue
- [ ] PR is not very big (about 200-400 lines of change ideally)
- [ ] Adds or updates tests
- [ ] Tested manually (bot responds, sync runs, charts render)
- [ ] No new mypy errors (`uv run mypy`)
- [ ] Ruff clean (`uv run ruff check .`)
- [ ] New environment variables added to Railway and `.env.example` (if any introduced)
- [ ] Alembic migration included if schema changed

### Demo screenshots or video, if any
```
