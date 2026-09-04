# Sprint 10 — Three roles, a simulated login, and user management

**Status:** ✅ Done
**Created At:** 2026-09-04
**Gate:** G8 — Final QA · **Deadline:** 17 September 2026
**Owner:** M1 — Engine & API (backend) · M2 — Product & UX (frontend)
**Source:** [ADR-0006](../../../docs/canonical/decisions/ADR-0006-three-roles-and-simulated-login.md) · `docs/canonical/07_privacy_threat_model.md` § Product controls · `docs/canonical/03_architecture.md` § Security

## Goal

One role model with three names instead of four lists that disagree, enforced on the server
rather than in the sidebar; a login that is credential-shaped and honest about being persona
selection; and one administrative page that proves separation of duties by never touching a case.

## Acceptance

- Exactly three roles — `reviewer`, `senior_reviewer`, `admin` — defined in one place
  (`app/service/access.py`) and derived from there by `disposition.py`, the menu, and the guard.
- Every ❌ in the ADR-0006 § 2 matrix is a **server** refusal with a stable error code, asserted
  against every protected endpoint with a forged `X-Actor-Role`.
- `admin` is refused the queue, case detail, disposition, reopen, case audit, ingest, screen,
  evaluation and briefing. `reviewer` is refused a reopen; `senior_reviewer` is allowed one.
- An administrator may not change their own role or deactivate themselves — refused on the
  server with `USER_SELF_MODIFICATION_REFUSED`.
- A deactivated account cannot start a session; a wrong passcode is refused and no response
  anywhere echoes a passcode.
- Every user-management change appends an event carrying actor, target, and both values, to an
  append-only table with the same trigger the case audit uses.
- The seeded roster is exactly three, and `demo_reset.py` restores a roster a demo toggled.
- **The seven frozen endpoints and the briefing endpoint do not move.** Three additive paths.
- `/login` **is** the ADR-0006 § 2 access matrix, generated from the server and drift-tested; it
  fits one viewport without scrolling, carries permanent `AKUN SIMULASI` and `DATA SINTETIK`
  badges, claims no security, and uses no imagery belonging to anyone else.
- The sidebar renders from `src/config/menu/app-menu.ts` filtered by role; a route the role may
  not reach redirects rather than rendering.
- Logging out with an unsaved disposition draft warns before discarding it.

## Scope (stacks involved)

- [x] backend → see [`backend/`](./backend/) · [x] frontend → see [`frontend/`](./frontend/)

## Constraints (non-negotiable — apply to every task in this sprint)

Source: `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` § 20 *Important constraints*.

- One official category: *Efisiensi Risiko pada Fasilitas Kesehatan*.
- **Synthetic data only.** No real JKN participant data, in any form, for any reason.
- The decision stays with a human. No automatic claim rejection, payment action, sanction, or code change.
- Language is **"risk / anomaly requiring review"** — never "fraud" as a finding.
- **No LLM anywhere in the risk score or status transition.**
- No production-integration claim. **No claim that this login authenticates anyone.**
- Source, resource, and version provenance is preserved on every derived artifact.
- Every metric quoted in the proposal comes from a generated artifact, never typed by hand.

## Outcome

Landed 4 Sep 2026. Verified: backend **505** (was 467) · web **236** (was 184) · playwright **40**
(was 24) · tsc clean · ruff clean · domain 23 · data 57 · model 71 · evaluation 47 unchanged.
Alembic head `f2b8e91c60a7`; `docs/api/openapi.json` regenerated (twelve `/v1` paths — the seven
frozen, the briefing, and four additive). One existing test changed: the reopen case in
`test_disposition.py` swaps the retired `auditor` for `senior_reviewer`; what it asserts is
untouched.

## Kill criteria

See ADR-0006 § Kill criteria. The first one is the one to watch: **if the login page reads as a
security claim to any non-domain reader, the badge and copy have failed** and the page reverts to
a plain persona picker while the RBAC stays.
