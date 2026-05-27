---
name: lint-check
description: Run lint, format, type-check, security, and test checks — same gates as CI. Invoke before committing or pushing.
model: haiku
version: 1.0.0
---

# Lint Check

Run these checks in order from the project root. Fix every failure before moving on.

## 1. Ruff auto-fix

```bash
uv run ruff check --fix .
```

Resolves import sorting, deprecated typing syntax, and other mechanical issues automatically.

## 2. Ruff format

```bash
uv run ruff format .
```

## 3. Fix remaining ruff violations

```bash
uv run ruff check --statistics .
```

Work through each remaining violation file by file.

### D100 / D101 / D102 / D103 / D106 — missing docstrings

Add a one-line Google-style docstring to every flagged public module, class, method, or function:

```python
"""Short description."""
```

Rules:
- One sentence, ends with a period.
- Describes **what** the thing is or does — not how.
- Never add `Args:` sections (not required).
- Never add `Raises:` sections (`DOC501` is ignored).
- Do not add docstrings to private members (`_name`) or `__init__` methods.
- Do not rewrite existing docstrings — only add where missing.

### E501 — line too long

Wrap long imports with parentheses. Wrap long function signatures with one param per line.

### RUF029 — unused async

Remove `async` from functions that don't `await` anything.

## 4. Verify clean

```bash
uv run ruff check .
```

Zero violations.

## 5. Mypy

```bash
uv run mypy
```

Fix all type errors. Never use `# type: ignore` to silence — fix the code.

## 6. Pip-audit

```bash
uv run pip-audit --skip-editable
```

If vulnerabilities are found, report them and stop.

## 7. Tests

```bash
uv run pytest tests/ -q
```

All tests must pass. If any fail, stop and report which test and why.

## Rules

- Never use `# noqa` to silence lint — fix the code.
- Never use `# type: ignore` to silence mypy — fix the code.
- Line length limit is 88 characters.
- Report results as: `lint ✓ | format ✓ | mypy ✓ | audit ✓ | tests ✓ — N passed`.
