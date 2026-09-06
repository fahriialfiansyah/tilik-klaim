# Sprint 11 — Bilingual UI: one product, two languages

**Status:** ✅ Done
**Created At:** 2026-09-06
**Gate:** G8 — Final QA · **Deadline:** 17 September 2026
**Owner:** M1 — Engine & API (backend) · M2 — Product & UX (frontend)
**Source:** Owner request, 6 September 2026 — a language switch in the header, and an English rendering of the product beside the Indonesian one.

## Goal

Every screen readable in English as well as Indonesian, chosen from one control in the header,
**without any screening result changing**. Indonesian stays the working language and the default;
English is a second rendering of the same catalog, never a second catalog.

## Acceptance

- One switch, in the app header and on `/login`, naming each language in its own language.
- The choice persists across visits and is mirrored onto `<html lang>` for screen readers.
- **Reasons and counter-evidence are rendered from the backend catalog by code**, not composed
  in the client and not read off the stored sentence — so an existing case is readable in
  English without being re-screened.
- A case read in either language carries the same reasons, evidence, component scores, band and
  numbers. Only the prose differs.
- The two locale trees hold exactly the same keys, and every sentence needing a fact needs it in
  both languages.
- No wording in either language states fraud, and no English reason says what someone *did*
  rather than what the record shows.
- `NO_OBSERVED_RISK` is never named "clean" or "safe" in either language.
- Indonesian remains the default for a missing, malformed, or unsupported `Accept-Language`.

## Scope (stacks involved)

- [x] backend → see [`backend/`](./backend/) · [x] frontend → see [`frontend/`](./frontend/)

## Constraints (non-negotiable)

Unchanged from every prior sprint, and one of them is why this sprint is shaped the way it is:

- Language is **"risk / anomaly requiring review"** — never "fraud" as a finding. English makes
  that easy to lose, so the constraint is asserted per-locale rather than once.
- Absence of evidence is **not** evidence a service was not delivered. `"no completed procedure
  record"` and `"the procedure was not performed"` are a short edit apart and only the first is
  a claim this system may make; a test forbids the second shape.
- **No contract change.** No endpoint moved, no response field was added or removed. The locale
  travels on `Accept-Language` and nothing else.
- Synthetic data only; the decision stays with a human; no LLM in the risk path.

## Notes

The locale is a property of the *reader*, not of the case — so it travels on a header rather
than in the URL. A `?lang=` parameter would give one case two URLs and the cache two answers to
the same question.
