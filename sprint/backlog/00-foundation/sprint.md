# Sprint 00 — Foundation

**Status:** 📋 Planned
**Created At:** 2026-08-30
**Started At:** -
**Completed At:** -
**Gate:** — (enabler for G3)
**Deadline:** 31 Agustus 2026
**Owner:** M1 — Technical & AI

## Goal

Repository, tooling, local stack, and canonical docs are wired so every later sprint has a
place to land and a command to verify itself.

## Acceptance

A teammate clones the repo, runs three documented commands, and gets: a Postgres container
up, the API answering `/healthz` with its engine identity, and the web app serving four
routes. Backend tests and web typecheck both pass.

## Scope (stacks involved)

- [x] frontend → see [`frontend/`](./frontend/)
- [x] backend → see [`backend/`](./backend/)
- [ ] agent — none in this project
- [ ] mcp — none in this project
- [ ] mobile — none in this project

## Workforce members touched

- `be_service` — API skeleton, configuration, health probe, test harness
- `fe_shell` — app shell, config-driven menu, four route stubs

## Cross-stack dependencies

No shared data yet — stacks can run in parallel.

## Constraints (non-negotiable — apply to every task in this sprint)

Source: `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` § 20 *Important constraints*.

- One official category: *Efisiensi Risiko pada Fasilitas Kesehatan*.
- **Synthetic data only.** No real JKN participant data, in any form, for any reason.
- The decision stays with a human. No automatic claim rejection, payment action, sanction, or code change.
- Language is **"risk / anomaly requiring review"** — never "fraud" as a finding.
- **No LLM anywhere in the risk score or status transition.**
- No production-integration claim. No live BPJS / SATUSEHAT / E-Klaim connection.
- Source, resource, and version provenance is preserved on every derived artifact.
- Every metric quoted in the proposal comes from a generated artifact, never typed by hand.

## Notes

The scaffold service referenced by `.claude/skills/bootstrap-project` sits on an internal
office network and is unreachable from this machine (verified 2026-08-30: connection
timeout). This is a personal project, so it will stay unreachable. The apps here were
scaffolded by hand with standard tooling instead.

**Do not run `.claude/skills/bootstrap-project/scripts/init_boilerplate.sh` later**, even
from inside that network — it unzips with `-o` and would overwrite `apps/` without warning.

## Outcome

(Filled in when the sprint moves to `archive/`.)
