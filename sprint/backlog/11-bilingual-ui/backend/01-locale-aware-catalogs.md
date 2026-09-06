# Task 01 — Locale-aware reason and note catalogs, negotiated per request

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** yes
**Autonomous:** yes
**Depends on:** —

## Files to touch

- `packages/domain/src/tilik_domain/locale.py` — **new**: `Locale`, `DEFAULT_LOCALE`, `negotiate`
- `packages/domain/src/tilik_domain/notes.py` — **new**: the counter-evidence catalog
- `packages/domain/src/tilik_domain/reasons.py` — `sentence_en`, `ReasonDefinition.sentence()`
- `apps/backend/app/service/text.py` — **new**: the connective text the API composes itself
- `apps/backend/app/router/locale.py` — **new**: the `Accept-Language` dependency
- `apps/backend/app/service/rules/registry.py` — `CounterEvidence.of()`, `note_code`, `render()`
- `apps/backend/app/service/rules/{phantom,repeat,unbundling,clone_baseline}.py`
- `apps/backend/app/service/{case_query,case_loader}.py`
- `apps/backend/app/router/{cases,bundles}.py`

## TODOs

- [x] `Locale` with two members and Indonesian as `DEFAULT_LOCALE`
- [x] `negotiate()` honours weights, matches on the primary subtag (`en-GB` → `en`), treats
      `q=0` as a refusal, and falls back to Indonesian for `*` and for anything unsupported
- [x] `sentence_en` on all seven reasons; `sentence(locale)` is the only accessor
- [x] **Counter-evidence became a catalog.** Eleven notes were literal f-strings inside the four
      rule modules — composed at screening time and frozen into the stored case, so an English
      reader would have had Indonesian arguments beside English findings
- [x] `CounterEvidence.of(code, **params)` builds from the catalog; the rules no longer hold a
      second copy of any sentence, which removed ~60 lines of duplicated literals
- [x] `note_id` kept as the stored Indonesian text, so cases screened before the catalog stay
      readable and every existing assertion keeps holding
- [x] Reason sentences resolved **by `hit.code`**, never off the stored `sentence_id` — an old
      case is readable in English without re-screening it under a newer ruleset
- [x] Band basis, caps, timeline labels and the no-risk row moved to `app/service/text.py`
- [x] `RequestLocale` injected into `/v1/cases`, `/v1/cases/{id}` and `POST …/screen`
- [x] English plural handled in one place; Indonesian needs none
- [x] 8 endpoint specs asserting only the prose moves, plus 22 domain specs on the two catalogs
- [x] Existing suite green with no assertion edited — the Indonesian is byte-identical because
      it now comes from the catalog the rules used to inline

## Acceptance

The same case read with `Accept-Language: en` and with `id` carries identical reason codes,
evidence, `expected_support`, component scores, band and `deterministic` flags, and a different
`sentence`. A French header reads as Indonesian. `test_rules_gold.py` passes untouched.

## Notes

`sentence_id` was always the Indonesian sentence, not an identifier — the `_id` is a locale tag.
That made `sentence_en` the natural pair rather than a new concept.
