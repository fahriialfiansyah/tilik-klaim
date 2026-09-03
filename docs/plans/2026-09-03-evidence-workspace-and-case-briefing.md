# Implementation Plan — Evidence Workspace + bounded Case Briefing

**Date:** 2026-09-03 · **Branch:** `development` · **Status:** awaiting owner approval
**Decisions:** [ADR-0004](../canonical/decisions/ADR-0004-evidence-workspace.md) ·
[ADR-0005](../canonical/decisions/ADR-0005-bounded-case-briefing.md)

Two phases. **Phase A is independent and can ship alone.** Phase B depends on A landing and on
Gate 6 being formally signed off, and is designed so that removing it is a clean revert.

---

## 0. Verified baseline (measured today, not quoted from HANDOVER)

```
apps/backend      338 passed        packages/domain    23 passed
packages/data      57 passed        packages/model     71 passed
evaluation         47 passed        apps/web (vitest) 107 passed
ruff: All checks passed!            tsc --noEmit: silent
playwright: 17 specs (needs API + web + fresh seed; not run in this session)
```

`HANDOVER.md` § 2 quotes 312 backend and 91 web. Both are stale; the numbers above are the
gate. Every phase below must end on these counts **plus** its own new tests, with nothing
subtracted.

Two facts that shape the whole plan:

- `docs/` is gitignored. The three existing ADRs are tracked from before that rule. **New files
  under `docs/` need `git add -f`** or they are invisible to the owner's morning review.
- `apps/backend/tests/fixtures/api/*.json` are committed contract fixtures the frontend builds
  against. Any DTO change rewrites them. Phase A changes none.

---

## PHASE A — Evidence Workspace (`/cases/:id`)

**No API change. No DTO change. No token change. No fixture change.** Every value the four views
render already ships in `CaseDetailResponse`.

### A.1 Files affected

| File | Change | Est. |
|---|---|---|
| `apps/web/src/features/review/case-detail/store.ts` | **Edit.** Add a `workspace` slice: `selection {reasonCode, lineId}` and a `drawer` discriminated union. Draft state and its lifetime are untouched. | 0.3 d |
| `apps/web/src/features/review/case-detail/selectors.ts` | **Edit.** Add `buildEvidenceMatrix()`, `swimlanes()`, `mapForReason()`, `linesForReason()`. Existing four selectors keep their signatures. | 0.5 d |
| `.../components/EvidenceMatrix.tsx` | **New.** Widget 28. Real `<table>`, four cell states, text labels on every state. | 0.6 d |
| `.../components/EvidenceMap.tsx` | **New.** Widget 15, re-shaped. Replaces `EvidencePath.tsx`. | 0.5 d |
| `.../components/EvidencePath.tsx` | **Delete** once `EvidenceMap` is green. Kept in git history as the revert target. | — |
| `.../components/EpisodeSwimlane.tsx` | **New.** Widget 14, re-shaped. Replaces `EpisodeTimeline.tsx`. | 0.5 d |
| `.../components/EpisodeTimeline.tsx` | **Delete** once the swimlane is green. | — |
| `.../components/CaseDrawerHost.tsx` | **New.** One host rendering source *or* comparison from the store union. Owns focus return. | 0.4 d |
| `.../components/SourceDrawer.tsx` | **Edit.** Becomes a presentational child of the host; keeps `useLastPresent` and its four availability states verbatim. | 0.2 d |
| `.../components/ComparisonDrawer.tsx` | **Edit.** Same — keeps the template caveat at the top, the candidate link, and the redaction comments. | 0.2 d |
| `apps/web/src/pages/case-detail/CaseDetailPage.tsx` | **Edit.** Composition only. Five `useState` hooks collapse into the store; `openSource`/`openComparison` removed. | 0.4 d |
| `.../case-detail/labels.ts` | **Edit.** Indonesian labels for the four cell states, four lane names, map node captions. | 0.2 d |
| `sprint/00-app-spec.md` | **Edit.** Add widget 28; re-word 14 and 15. Display rules 1–5 unchanged. | 0.2 d |
| `design/DESIGN.md` | **Edit.** One line under *Berkas desain*: the annotation map for `/cases/:id` now has a workspace to annotate. | 0.1 d |
| `changelog/web.md` | **Append.** | 0.1 d |

### A.2 Data derivation (all client-side, from existing fields)

```
Matrix rows      ← detail.lines
Matrix columns   ← unique(reasons.flatMap(r => r.expected_support)), catalog order
Cell(line, type) ← reasons citing that line (evidence ∋ ClaimLine:line_id)
                   ├ expects type & has ref & source.availability ∈ {PRESENT, RELATED_BUNDLE} → FOUND
                   ├ expects type & has ref & source.availability === MISSING                 → UNRESOLVED
                   ├ expects type & no ref                                                    → MISSING
                   └ no citing reason expects type                                            → NOT_EXPECTED
Lanes            ← timeline events grouped by kind (encounter | procedure | medication)
                   + a fourth lane derived from detail.lines[].service_at   (Penagihan)
Map(reason)      ← claim → cited ClaimLine(s) → cited Encounter → one terminal per
                   expected_support type; counter-track from counter_evidence_notes
```

`missingEvidenceTypes()` — which drives the request-evidence checklist — reads the *same* two
fields, so the checklist and the Matrix cannot tell different stories. That equivalence gets a
test.

### A.3 UI states (five, per `design/DESIGN.md`)

| State | Matrix | Swimlane | Map | Drawer |
|---|---|---|---|---|
| **Memuat** | existing `CaseDetailLoading` skeleton covers the whole workspace | — | — | closed |
| **Kosong** | no reasons → *"Tidak ada risiko teramati"*; no lines → *"Bundel ini tidak memuat baris tagihan"* | *"…tidak memuat kejadian yang dapat diurutkan"* (existing copy) | *"Belum ada alasan yang ditelusuri"* (existing copy) | n/a |
| **Galat** | existing `CaseDetailFailed` + retry | — | — | unresolvable ref → drawer opens on `MISSING` and says so |
| **Nonaktif** | cells are non-interactive when a case is `DISMISSED`/`CONFIRMED`; still readable | same | same | still openable — reading history is never disabled |
| **Versi usang** | existing `VersionConflictBanner` above the workspace; workspace stays rendered so the reviewer can see what changed | | | drawer forced closed on reload |

Empty ≠ absent, everywhere: a `NOT_EXPECTED` cell and a `MISSING` cell must never look alike, and
neither may be conveyed by colour alone.

### A.4 Guardrails

- `EvidenceMatrix` and `EvidenceMap` are **pure functions of the DTO** — no fetch, no store write.
- The Map asserts its own shape: a dev-only invariant that no node has two parents and no
  terminal links to another terminal (display rule 3, made mechanical).
- Counter-evidence stays in `ReasonCard`, outside the collapsible. A test asserts it is in the
  DOM with the card collapsed (this test exists; it must keep passing unmodified).
- The drawer union makes "both open" unrepresentable rather than merely unlikely.
- Focus return stays explicit: the store records the id of the element that opened the drawer,
  and the host restores focus to it on close. Radix's own restore stays `preventDefault`ed —
  the trap recorded in `HANDOVER.md` § 5.

### A.5 Test cases

**Vitest (new — target ≈ 22 tests):**

| Test | Asserts |
|---|---|
| `EvidenceMatrix.test.tsx` — a line expecting Procedure with none cited renders `MISSING` | the core phantom cell |
| … a line whose reason cites a ref whose source is `MISSING` renders `UNRESOLVED`, not `MISSING` | defect ≠ absence (display rule 4) |
| … a type no citing reason expects renders `NOT_EXPECTED` and is labelled for screen readers | empty ≠ absent |
| … every non-empty cell exposes a text label, not only a colour class | `DESIGN.md` accessibility floor |
| … a case with zero reasons renders the "tidak ada risiko teramati" copy, never "bersih"/"aman" | canonical wording |
| `selectors.test.ts` — matrix `MISSING` set equals `missingEvidenceTypes()` | checklist and matrix agree |
| `EpisodeSwimlane.test.tsx` — an empty *Tindakan* lane renders the lane with an explicit empty label | the phantom picture |
| … lane order is fixed and events stay in time order within a lane | |
| … every event resource still renders an `EvidenceRefButton` | display rule 4 |
| `EvidenceMap.test.tsx` — one trunk; terminal count equals `expected_support.length` | display rule 3 |
| … a found terminal is openable; an absent terminal is a labelled dead end | |
| … counter-evidence renders on a visually distinct track and is labelled as counter-evidence | display rule 2 |
| … with no reason open, the map makes no claim about missing clinical evidence | the regression already fixed once in `EvidencePath`; carried forward |
| `store.test.ts` — opening a comparison closes an open source drawer | mutual exclusion |
| … changing the selected reason closes a drawer opened from the previous reason | synchronisation |
| … opening or closing a drawer never mutates the disposition draft | separation |
| `ComparisonDrawer.test.tsx` / `SourceDrawer.test.tsx` | existing tests pass **unmodified** against the new host |

**Playwright (existing 17 must stay green; 2 new):**

- `a drawer traps focus, closes on Escape, and hands focus back to its trigger` — must pass with
  the unified host and with the trigger being a **matrix cell** and a **map terminal**.
- `every evidence reference is reachable and states what it is` — now also walks matrix cells,
  swimlane events and map terminals.
- **New:** the whole workspace is operable by keyboard, matrix cell → drawer → Escape → cell.
- **New:** the 25–50 s evidence beat completes within its slot on a seeded phantom case.

**Manual QA:** `docs/qa/2026-09-0X-evidence-workspace/` with numbered screenshots of all five
states in both themes, appended to `docs/qa/MANUAL-QA.md`. This is what the owner checks by eye.

### A.6 Effort

**≈ 4.3 days** of the itemised work above, ≈ **3.0–3.5 days** realistic with the tests written
first and the QA pass at the end.

---

## PHASE B — Bounded read-only Case Briefing

**Preconditions:** ADR-0005 approved · Gate 6 flipped to ✅ in `sprint/01-sprint-planning.md` ·
Phase A landed and green.

### B.1 Files affected — backend

| File | Change | Est. |
|---|---|---|
| `apps/backend/app/dto/briefing.py` | **New.** `BriefingObservation`, `BriefingQuestion`, `CaseBriefing`, and the five SSE event models. All `frozen=True, extra="forbid"`. | 0.4 d |
| `app/service/briefing/__init__.py` | **New.** Public surface: `build_briefing(case_id) -> CaseBriefing` and `stream_briefing(case_id)`. | 0.1 d |
| `app/service/briefing/tools.py` | **New.** The seven read-only tools + their JSON schemas. Closed registry; an unknown name is refused before dispatch. | 0.6 d |
| `app/service/briefing/template.py` | **New.** The deterministic, LLM-free briefing. Pure functions over `CaseDetailResponse`. | 0.5 d |
| `app/service/briefing/validation.py` | **New.** The five-gate validator of § B.4. | 0.5 d |
| `app/service/briefing/loop.py` | **New.** Bounded tool-calling loop: ≤ 8 tool calls, wall-clock timeout, token cap, one terminal step. | 0.6 d |
| `app/service/llm_provider.py` | **New.** The only place in the repo that talks to a model. **Superseded 4 Sep:** the official `openai` SDK against the internal vLLM gateway, with typed error mapping and a guided-decoding path for gateways that do not serve tool calling. | 0.4 d |
| `app/router/briefing.py` | **New.** `GET /v1/cases/{case_id}/briefing` — SSE, plus `?stream=false`. | 0.4 d |
| `app/main.py` | **Edit.** One `include_router` line. | — |
| `app/config.py` | **Edit.** `briefing_enabled=False`, plus the gateway values. **Superseded 4 Sep:** shipped against the internal vLLM gateway as `llm_model_vllm` / `vllm_base_url` / `vllm_api_key` (`SecretStr`, no defaults, start-up validation), not a third-party host. See ADR-0005 § *The gateway, as implemented*. | 0.2 d |
| `app/errors.py` | **Edit.** Append `BRIEFING_UNAVAILABLE`. Existing codes untouched — appending is safe, repurposing is not. | 0.1 d |
| `apps/backend/pyproject.toml` | **Edit.** Promote `httpx>=0.28` from `dev` to runtime. | — |
| `apps/backend/.env.example` | **Edit.** The five new keys, all optional, key blank. | 0.1 d |
| `docs/api/openapi.json` | **Regenerate** via `scripts/export_openapi.py`. | — |

### B.2 Files affected — frontend

| File | Change | Est. |
|---|---|---|
| `apps/web/src/features/review/case-briefing/types.ts` | **New.** Mirrors the DTOs, snake_case kept. | 0.2 d |
| `.../case-briefing/api.ts` | **New.** `EventSource` on the relative `/v1` path + a `?stream=false` fallback fetch. | 0.3 d |
| `.../case-briefing/useCaseBriefing.ts` | **New.** Idle → streaming → done → failed. Never auto-starts. | 0.3 d |
| `.../case-briefing/components/BriefingPanel.tsx` | **New.** Collapsed, below the reasons, no action controls. | 0.5 d |
| `.../case-briefing/components/BriefingProgress.tsx` | **New.** The tool-call log — the transparency artifact. | 0.3 d |
| `.../case-briefing/labels.ts` | **New.** Indonesian copy, including the non-authoritative framing. | 0.2 d |
| `apps/web/src/pages/case-detail/CaseDetailPage.tsx` | **Edit.** One slot below the reason rail. | 0.1 d |
| `changelog/{backend,web}.md` | **Append.** | 0.1 d |

### B.3 API / schema

**One additive endpoint. The seven frozen contracts are untouched.**

```
GET /v1/cases/{case_id}/briefing
    ?stream=true|false      (default true)
  200 text/event-stream  |  200 application/json (CaseBriefing)
  404 CASE_NOT_FOUND
  200 + generated_by=TEMPLATE   when disabled, unconfigured, timed out, or rejected
```

`BRIEFING_UNAVAILABLE` is reserved for a genuinely broken service. A disabled or unconfigured
briefing is **not** an error — it is the template, which is the product's default state.

```python
class BriefingObservation(Dto):
    statement: str = Field(max_length=240)     # Indonesian, non-accusatory
    kind: ObservationKind                       # EVIDENCE_GAP | CORROBORATION | COUNTER_EVIDENCE
                                                # | COMPARISON | TIMELINE | COMPLETENESS
    source_refs: tuple[EvidenceRefDto, ...] = Field(min_length=1)   # validated, never empty
    reason_code: ReasonCode | None = None
    confidence: Literal["STATED", "INFERRED"]   # never numeric — a number is a second score

class BriefingQuestion(Dto):
    question: str; why_it_matters: str
    source_refs: tuple[EvidenceRefDto, ...] = Field(min_length=1)

class CaseBriefing(Dto):
    case_id: str; case_version: int
    observations: tuple[BriefingObservation, ...] = Field(max_length=5)   # § 12's five-sentence cap
    open_questions: tuple[BriefingQuestion, ...] = Field(max_length=3)
    uncertainty_note: str = Field(min_length=1)                            # mandatory
    generated_by: Literal["LLM", "TEMPLATE"]
    model_id: str | None; prompt_version: str
    validation_rejected: bool = False; rejection_reason: str | None = None
    versions: VersionStamp
```

SSE events, each a JSON-serialised model: `status` · `tool` · `observation` · `done` · `error`.

### B.4 Guardrails

**Structural (cannot be violated by a prompt):**

1. Seven tools, closed registry, all read-only, all slicing the one `CaseDetailResponse` already
   built for that case. No store, no bundle, no cross-case query, no network, no filesystem.
2. No write tool exists. `POST /v1/cases/{id}/dispositions` neither reads nor accepts a briefing.
3. Import direction is one-way and asserted: the risk path never imports the briefing.
4. Budgets: ≤ 8 tool calls, wall-clock timeout, output token cap, one model.

**Output validation — all five must pass or the whole briefing is rejected:**

1. every `source_refs` entry resolves in that case's source index;
2. every numeric literal in every sentence appears verbatim in the tool output supplied;
3. no forbidden term: `fraud`, `curang`, `palsu`, `tolak`, `sanksi`, `terbukti`, `pasti`,
   `bersih`, `aman`, `bayar`, `denda`;
4. counts and lengths within cap;
5. `uncertainty_note` non-empty.

**Presentational:**

6. Panel below the reasons, collapsed by default, no action controls, no draft coupling.
7. Labelled non-authoritative; the raw reasons are always on the same screen.
8. No robot head, no sparkle (`design/DESIGN.md`).

### B.5 Fallback without an LLM

Default. `BRIEFING_ENABLED=false` ships a template briefing built by pure functions:

- one observation per reason — its catalog sentence plus the `expected_support` gap, refs = that
  reason's own evidence;
- one `COMPLETENESS` observation when the case carries completeness notes;
- one `COUNTER_EVIDENCE` observation per reason that has notes, refs = the note's refs;
- questions derived from the same missing-evidence set the checklist uses;
- a fixed `uncertainty_note` from the catalog.

Every sentence is already-approved catalog text or a template over it, so it is
`test_no_rule_ever_uses_the_word_fraud`-safe by construction. This path is what runs in the
offline demo, and it is the path that ships if the LLM is killed.

### B.6 Test cases

**Backend (new — target ≈ 40 tests):**

| Test | Asserts |
|---|---|
| `test_the_risk_path_never_imports_the_briefing` | AST walk over `screening.py`, `service/rules/*`, `disposition.py`, `case_query.py` — no import of `briefing` or `llm_provider`. **The single most important test in this plan.** |
| `test_briefing_module_names_no_scoring_identifier` | AST walk of the briefing package: no `band`, `score`, `priority`, `disposition`, `state_after` assignment |
| `test_every_tool_is_read_only` | each of the seven returns a frozen model; no store or session is reachable from the module |
| `test_unknown_tool_name_is_refused_before_dispatch` | closed registry |
| `test_tools_cannot_see_more_than_the_screen` | tool output ⊆ `CaseDetailResponse` for the same case |
| `test_related_bundle_redaction_survives_the_tool_surface` | no peer narrative, no peer token |
| `test_observation_without_source_refs_is_rejected` | gate 1 |
| `test_unresolvable_source_ref_rejects_the_whole_briefing` | gate 1, whole-object rejection |
| `test_a_number_not_present_in_tool_output_rejects_the_briefing` | gate 2 |
| `test_forbidden_terms_reject_the_briefing` (parametrised over all 11) | gate 3 |
| `test_rejection_falls_back_to_the_template_and_says_so` | `generated_by=TEMPLATE`, `validation_rejected=True` |
| `test_template_briefing_needs_no_network` | monkeypatched-to-explode provider; still returns |
| `test_template_briefing_uses_no_forbidden_word` (over all 5 gold fixtures) | mirrors the existing rules test |
| `test_disabled_briefing_is_not_an_error` | 200 + template, not 5xx |
| `test_timeout_and_transport_failure_both_fall_back` | no partial prose escapes |
| `test_tool_call_budget_is_enforced` | loop bound |
| `test_sse_emits_status_tool_observation_done_in_order` | contract of the stream |
| `test_stream_false_returns_the_same_object_as_the_stream_terminal` | the two paths agree |
| `test_briefing_for_unknown_case_is_404` | |
| `test_every_frozen_endpoint_is_now_implemented` | **existing, must pass unchanged** |
| `test_no_action_triggers_payment_rejection_or_sanction` | **existing, must pass unchanged** |
| Contract fixture drift tests | **existing, must pass unchanged** — no fixture is rewritten |

**Frontend (new — target ≈ 10 tests):**

- panel is collapsed on mount and never auto-fetches;
- panel renders below the reason rail in DOM order (reason before summary);
- panel exposes no button that sets an action, a structured reason, or a checklist item;
- generating a briefing does not mutate the disposition draft;
- `TEMPLATE` provenance is stated on screen, not hidden;
- every observation's refs render as openable `EvidenceRefButton`s;
- SSE progress renders each `tool` event in arrival order;
- stream failure degrades to the `?stream=false` fetch and says so;
- `role="status"`/`aria-live` announces progress without stealing focus;
- no icon in the panel is a robot or a sparkle (asserted on the icon set imported).

**Playwright (1 new):** the offline demo route still completes with `BRIEFING_ENABLED=false`.

### B.7 Effort

**≈ 5.4 days** itemised, ≈ **4.0–4.5 days** realistic. Phase A + Phase B ≈ **7–8 working days**.

---

## Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | **The Map drifts into a network** and breaks display rule 3 — the rule most easily broken by a well-meaning addition | Medium | High — a binding spec rule | The dev-only single-parent invariant in A.4; the kill criterion in ADR-0004 |
| 2 | **The Matrix becomes the first thing read**, displacing the reason sentence and failing `DESIGN.md`'s comprehension test | Medium | High — that test is a kill criterion in `01_product_decision.md` | Matrix sits below the reason rail; the 30-second reader check is run before merge, not after |
| 3 | **SSE does not survive the rsbuild dev proxy** (buffering or compression) | Medium | Medium | `X-Accel-Buffering: no`, no gzip on the route, and the `?stream=false` path is a first-class fallback, not a patch |
| 4 | **The LLM writes a plausible sentence the evidence does not support** — the exact failure `01_product_decision.md` attributes to a generic LLM copilot | Medium | **Critical** — this is a false-accusation risk | Whole-object rejection on any of five gates; template fallback; the 1-in-20 kill criterion |
| 5 | **The panel makes the product read as an AI fraud detector**, hitting an existing kill criterion | Low–Medium | **Critical** — it would end the entry's differentiation | Collapsed, below, non-authoritative, no robot/sparkle; re-run the three-reader test with the panel present |
| 6 | Adding an eighth endpoint disturbs a frozen-contract test | Low | Medium | Pre-flight check: `test_every_frozen_endpoint_is_now_implemented` asserts three paths are not 501; it does not count routes. Verified. |
| 7 | Regenerating `openapi.json` produces a large diff nobody reviews | Low | Low | One scripted regeneration, in its own commit |
| 8 | **Schedule.** ~7–8 days against three outstanding Gate-6 sign-offs, the 1080p recording and the 3-minute rehearsal, with the proposal due 19 Sep | **High** | High | Phase A ships alone and is the higher-value half. Phase B is explicitly droppable — that is why the phases are separable |
| 9 | New `docs/` files stay invisible to git | High | Low | `git add -f` for both ADRs and this plan |
| 10 | `httpx` moves from dev to runtime dependency | Low | Low | Already installed and exercised by the existing test client |

---

## Kill criteria (consolidated)

Full tables sit in each ADR. In one line each:

**Phase A** — remove the Matrix if three non-domain readers cannot answer *"which line is missing
what?"* in 30 s · revert the Map if it reads as a network or any node gains two parents · revert
the workspace if the 25–50 s demo beat overruns · fall back to the flat timeline if four lanes
push a normal episode below the fold.

**Phase B** — disable the LLM if ≥ 1 in 20 briefings is rejected for an unsupported reference or
number · remove the panel if any reader calls the product a chatbot or an AI fraud detector ·
drop it if p95 latency exceeds 8 s or it delays the reasons painting · **keep the template and
remove the LLM if readers cannot tell them apart** — the same honest outcome the ML layer was
built to accept, and not a feature kill · revert immediately and without discussion if the
import-direction test ever fails.

---

## Order of work

1. ADR-0004 + ADR-0005 approved by the owner. ← **you are here**
2. Phase A, TDD, one Conventional Commit per component. QA screenshots. All counts reported.
3. Sprint 06 sign-offs completed; `sprint/01-sprint-planning.md` flipped to ✅.
4. Phase B, TDD, template path first and complete **before** any LLM code is written — so the
   product is shippable at every commit and the LLM is provably additive.
5. Regenerate `openapi.json`. QA screenshots. All counts reported.
6. Update `HANDOVER.md` (its counts are already stale) and `CONTINUE-PROMPT.md`.

Nothing is pushed to the remote. Sprint files are created only after approval, as
`sprint/backlog/08-evidence-workspace/{web,backend}/…`, following the existing task-file shape.
