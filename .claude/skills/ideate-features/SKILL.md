---
name: ideate-features
description: Brainstorm and prioritize new features for hermes-finance. Use when the user asks what to build next, wants ideas for improving the app, or wants to explore a specific area (data visibility, automation, integrations, UX). Produces actionable, sized ideas rooted in what's already in the codebase.
disable-model-invocation: false
---

You are helping plan improvements to **hermes-finance**, a personal fork of the Sure open-source finance app with a custom Monobank integration.

## What exists today

**Core app** (Rails 7.2, deployed on Railway):
- Transaction tracking with categories, tags, rules, merchants
- Balance sheet, cash flow Sankey chart, investment statements
- Period picker: 1D / 7D / MTD / 30D / 90D / YTD / 365D / All Time
- Multi-currency with historical FX rates
- External API at `/api/v1/` (accounts, transactions, categories, balances)
- Sidekiq + Redis for background jobs
- AI chat assistant

**Custom additions**:
- `monobank-sync/` — Python service that syncs Monobank → Rails via API (deployed on Railway)
- MCC-based auto-categorization for Monobank transactions
- Cashback posted as separate income transactions
- Pending/hold transaction flags via `extra["monobank"]["pending"]`
- Settings > Monobank page: sync status table + manual trigger button

**Data available from Monobank API** (not all utilized yet):
- MCC codes → merchant category
- `hold` flag → pending status
- `operationAmount` + `currencyCode` → FX transactions
- `cashbackAmount` → cashback income
- Account types: black, white, fop, platinum, iron, yellow
- Multiple accounts per client

## Idea format

For each idea produce:

```
### [Name]
**What**: One sentence.
**Why**: Why this matters for a personal finance app.
**Effort**: Small (< 1 day) / Medium (1–3 days) / Large (1+ week)
**Where**: Files/models to touch.
**First step**: The single next action to start.
```

## Idea areas — explore any of these when asked

### Data visibility
- Monthly salary detection (recurring large income, flag with label)
- FX exposure summary — how much is held in UAH vs USD/EUR
- Cashback earnings tracker — total cashback received this year
- Merchant spending heatmap — which merchants take the most money
- "Paycheck to paycheck" metric — days between income and balance hitting near-zero

### Monobank-specific
- Sync health dashboard — show last sync time, next scheduled, error count
- Hold/pending transaction reconciliation UI — see pending vs posted pairs
- Monobank statement PDF import fallback (for accounts not in sync)
- Per-account sync toggle — sync only selected Monobank account types

### Automation
- Auto-rule from MCC — "always assign MCC 5411 (grocery) to Groceries category"
- Recurring transaction detection for salary (already has job, needs UI)
- Budget alerts — notify when spending in a category exceeds threshold this month

### UX / personalization
- Default to "Last 365 Days" period for cash flow (migration written, needs `bin/rails db:migrate`)
- Pin favorite accounts to dashboard top
- Quick-add manual transaction from dashboard
- Dark/light mode toggle in header (settings exist, just surfacing it)

### Integrations (new data sources)
- Wise API — USD/EUR balance and transfers
- PrivatBank sync — another Ukrainian bank, similar Monobank pattern
- Google Sheets export — push monthly summary to a spreadsheet
- Telegram bot — daily balance summary notification

### Dev experience
- Per-session CLAUDE.md with current account IDs and API URL pre-filled
- Skill: `add-integration` — scaffold a new provider following the Monobank pattern
- Skill: `pre-pr` — run all CI checks locally before pushing

## Process

1. Ask one question first: **"What area — visibility, automation, integration, or UX?"**
2. Generate 3–5 sized ideas for that area.
3. After presenting ideas, ask: **"Want me to start on any of these now?"**
4. If yes, confirm scope and begin — don't ideate further, switch to implementation mode.
