# YouTube Automation — Project Memory (CLAUDE.md)

> Canonical context file for this project. Every Claude session working in this
> folder reads this first. Keep it short and current — details live in the
> other docs, this file just points to them.

## What this project is

Faceless YouTube automation at **zero cost** (no paid APIs, no paid tools).
Part of Abhi's income-independence plan (target: self-sustaining before
~Dec 2026–Jan 2027). YouTube's primary role: audience + income stream built
with automation doing the heavy lifting.

## Hard constraints

1. **Zero cost.** Free tiers, open-source, local tools only. Any paid tool
   needs an explicit decision recorded in DECISIONS.md.
2. **Automation-first.** Manual steps allowed only where automation is
   impossible (e.g. final upload review) — and must be listed in ARCHITECTURE.md.
3. **This server** (GCP, `/home/abhishek_niftytrader/youtube-automation/`) is the
   deployment target. Design for cron/systemd, not laptops.

## Doc map — where things live

| File | What it holds | Update when |
|---|---|---|
| CLAUDE.md | This file — entry point, constraints | Constraints/goals change |
| CONTEXT.md | Why, goals, niche, success metrics | Strategy changes |
| ARCHITECTURE.md | Pipeline stages, data flow, folder layout | Design changes |
| STACK.md | Zero-cost tool choices per stage + alternatives | Tool swapped/added |
| DECISIONS.md | Decision log (what we chose and why) | Any non-obvious choice |
| ROADMAP.md | Phases, current status, next actions | End of each work session |

## Current status

- **Phase 0: Foundation.** Docs created 2026-07-18. No code yet.
- Next: Abhi shares his existing git repos → we rank them → design Automation #1.

## Working rules for Claude sessions

- Read CLAUDE.md + ROADMAP.md at session start; skim others as needed.
- Record every non-obvious choice in DECISIONS.md (one line is fine).
- Update ROADMAP.md status before ending a work session.
- Never introduce a paid dependency silently.
