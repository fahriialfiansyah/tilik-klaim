> Status: canonical — read-only once accepted. Perubahan hanya lewat ADR baru.

# ADR-0005 — A bounded, read-only Case Briefing outside the risk path

- **Status:** Proposed — awaiting owner approval **and** formal Gate 6 sign-off
- **Date:** 2026-09-03
- **Scope:** One new service module inside `be_service` (`apps/backend/app/service/briefing/`), one additive endpoint, one collapsed panel on `/cases/:id`
- **Owner section:** [05_model_card.md](../05_model_card.md) § Optional LLM guardrails
- **Supersedes:** nothing. **Does not amend [ADR-0002](ADR-0002-no-llm-in-risk-score.md)** — it operates inside the escape hatch ADR-0002 itself defines, and every one of ADR-0002's five decisions continues to hold verbatim.

**Cross-reference (jangan salin isinya ke sini):**

- The exclusion this ADR must not touch, and the optional-summary clause it exercises → [ADR-0002](ADR-0002-no-llm-in-risk-score.md)
- The eight guardrails, verbatim and binding → [05_model_card.md](../05_model_card.md) § Optional LLM guardrails
- LLM-hallucination, prompt/data-leakage and false-accusation controls → [07_privacy_threat_model.md](../07_privacy_threat_model.md)
- Scope tiers — "Guarded LLM summary" sits in NICE TO HAVE → [01_product_decision.md](../01_product_decision.md) § 13
- "Never depend on a remote LLM" → [08_demo_runbook.md](../08_demo_runbook.md) § Demo reliability

---

## Context

The canon does not forbid this feature. It permits it, narrowly, and pre-writes its controls.

`05_model_card.md` § 12 decision table, verbatim, two rows:

> | Evidence summarization | Optional LLM after core works | Appropriate only for concise synthesis of supplied structured evidence with citations to resources. |
> | Investigation assistance | Optional, non-authoritative | May suggest questions or missing evidence; never change score/disposition. |

`ADR-0002` decision 3, verbatim: *"An LLM summary is **optional and post-Gate-6 only**."*
`01_product_decision.md` § 13 places "Guarded LLM summary" in **NICE TO HAVE**, not out of scope.

Three things in the canon *are* out of scope and are not what this ADR proposes.
Naming them precisely is the point of this section, because the word "agent" is doing a lot of
work and the canon uses it as shorthand for something else:

| Canonical exclusion | Where | Why this is not that |
|---|---|---|
| "GNN/blockchain/**multi-agent architecture**" | § 20, quoted in ADR-0002 | One in-process loop, one LLM, no second actor, no inter-agent protocol, no orchestrator. A multi-agent architecture is excluded and stays excluded. |
| "**generic chatbot**" | § 20, quoted in ADR-0002 | No conversation, no free-text input, no session, no follow-up turn. One request produces one structured object over one case, and the reviewer cannot type into it. |
| "Enterprise IAM, **streaming**, GNN, multi-agent system" | § 13 OUT OF SCOPE | That row lists platform infrastructure — it sits between enterprise IAM and GNN. Server-Sent Events reporting one request's own progress is a response encoding, not a streaming data platform. This reading is deliberate and is recorded here so it is reviewable rather than assumed. |

The `sprint/01-sprint-planning.md` Workforce Manifest holds only `be_service` and `fe_shell` and
states that **no agent roles exist**. This ADR does not create one: there is no
`apps/agents/<role>/` project, no Agno, no FastMCP, no MCP server, and no MCPHub registration.
The code is a module inside `be_service`, which is exactly the shape
`.claude/rules/architecture.md` already anticipates for "the backend's single bounded LLM call".

**Why now.** The core works, which was ADR-0002's precondition: 338 backend tests, four risk
modes firing, all seven frozen endpoints live, and the evaluation run producing artifacts. What
the screen still cannot do is tell a reviewer *what to read first* on a case with four reasons,
nine lines and thirty resources. That is "investigation assistance" as § 12 defines it, and § 12
permits it on condition it never changes the score or the disposition.

## Decision

Add **one bounded, read-only Case Briefing** to the backend, rendered as a collapsed panel on
`/cases/:id`.

### 1. It is architecturally incapable of reaching the risk path

- The briefing module imports from the risk path. **Nothing in the risk path imports the
  briefing module.** `screening.py`, `service/rules/*`, `disposition.py` and every store stay
  unaware it exists, and a syntax-tree test asserts that in both directions.
- No case field, no band, no reason, no component score, no state, no case version, and no audit
  event is written, derived from, or influenced by the briefing. It is computed *after* screening
  and *from* the screening result, never before or into it.
- Its output has no path to a status transition. The disposition endpoint neither reads it nor
  accepts it.

### 2. Its entire tool surface is a projection of the response the reviewer is already reading

The briefing may choose and call exactly seven local Python functions. Every one of them slices
the **already-built `CaseDetailResponse`** for that case — the same object `GET /v1/cases/{id}`
returns to the browser:

`get_case_overview` · `list_reasons` · `get_evidence_path` · `get_timeline` ·
`get_counter_evidence` · `get_comparison_candidate` · `get_source_resource`

This is the privacy argument, and it is structural rather than procedural: **the briefing cannot
see anything the reviewer cannot see on screen.** No store access, no raw bundle, no cross-case
query, no peer participant's narrative. `SourceAvailability.RELATED_BUNDLE` redaction already
applies because the redaction happened upstream, in `case_sources.build_source_index`.

There are **no write tools**, no search tool, no network tool, and no filesystem tool. The tool
list is closed and enumerated in code; a name not on the list is refused before dispatch.

### 3. Its output is Pydantic-structured, and every observation is source-bound

The model returns `CaseBriefing` — observations, open questions, and a mandatory uncertainty
note. Every `BriefingObservation` carries at least one `source_refs` entry, and a briefing whose
observations do not all carry one is rejected, not trimmed.

Confidence is `STATED` or `INFERRED`, never a number. A numeric confidence beside a risk band is
a second score, and reviewers anchor on scores — `07_privacy_threat_model.md` names that failure
directly ("Reviewer anchors on red score").

### 4. Validation is a gate, not a filter

Before a briefing leaves the service, all of the following must hold. Any failure rejects the
**entire** briefing and falls back to the deterministic template — nothing is partially accepted:

1. every `source_refs` entry resolves against that case's own source index;
2. every number appearing in any generated sentence appears verbatim in the tool output supplied
   to the model;
3. no forbidden term appears — the existing rules lexicon (`fraud`, `curang`, `palsu`, `tolak`,
   `sanksi`) plus terms that assert certainty or safety (`terbukti`, `pasti`, `bersih`, `aman`)
   and payment terms (`bayar`, `denda`, `klaim ditolak`);
4. observation and question counts are within cap, statements within length;
5. `uncertainty_note` is non-empty.

Guardrails 1–3 are `05_model_card.md`'s "reject output containing unsupported resource IDs or
numbers" and "never use 'fraud' as a finding", made executable.

### 5. It works with no LLM at all, and that is the default

`BRIEFING_ENABLED` defaults to **false**. With no key, no provider, a timeout, a transport
failure, or a rejected output, the service returns a **deterministic template briefing** composed
from the same DTO by pure functions, marked `generated_by: "TEMPLATE"`.

This is not a graceful-degradation nicety. `08_demo_runbook.md` § Demo reliability says *"Never
depend on a remote LLM"*, and the offline rehearsal is a Sprint 07 deliverable. A feature that
only works online could not appear in the demo at all.

### 6. Progress is streamed, and the stream is the transparency artifact

`GET /v1/cases/{case_id}/briefing` answers `text/event-stream`, emitting `status`, `tool`,
`observation`, `done`, and `error` events, each a JSON-serialised Pydantic model. The `tool`
events name every function the briefing chose to call, in order.

That log is not decoration. It is the answer to "what did it actually read", which is the
question an opaque summary cannot answer and the reason § 12 restricts summarisation to
"supplied structured evidence with citations". A `?stream=false` variant returns the same
`CaseBriefing` in one response for clients and tests that cannot consume SSE.

### 7. The human decision stays separate, visibly and structurally

- The panel renders **below** the reasons and **collapsed by default**. Reason before summary,
  always — `05_model_card.md`: "human sees the raw reasons beside the summary".
- The panel has **no action controls**. It does not select a disposition, does not prefill the
  structured reason, does not tick the requested-evidence checklist, and does not touch the
  draft in `store.ts`. A test asserts the briefing feature imports nothing from the disposition
  store.
- The panel is labelled as non-authoritative in working language, and carries the same synthetic-
  data framing as the rest of the screen.
- Icons stay within `design/DESIGN.md`: **no robot head, no sparkle**.

## Consequences

- ADR-0002 remains true in full. No LLM participates in the risk score; explanations are still
  produced by structured reason templates; the summary is optional, post-Gate-6, and never feeds
  a score or a status transition.
- The system gains an eighth endpoint. The seven frozen contracts are untouched, and
  `test_every_frozen_endpoint_is_now_implemented` continues to pass unchanged.
- `docs/api/openapi.json` must be regenerated once, via `scripts/export_openapi.py`.
- `05_model_card.md`'s guardrail list stops being a promise and becomes a test file.
- The failure mode this creates is **plausible prose exceeding the evidence** — the exact risk
  `01_product_decision.md` names for a "Generic LLM copilot". The validator is the control, and
  the kill criteria below are what happens if the control turns out to be insufficient.
- Reverting is a clean revert: one service package, one router, one DTO module, one frontend
  feature folder, one config block. Nothing else changes shape.

## Preconditions before this may merge

1. **Gate 6 formally signed off.** ADR-0002 says "post-Gate-6 only". Sprint 06's official run is
   done, but `sprint/01-sprint-planning.md` still reads 🚧 In Progress and three sign-offs remain.
   Substantive completion is not the same as the recorded gate, and this ADR's own precondition
   is the recorded one.
2. **Owner approval of this ADR**, since it introduces the first LLM call in the repository.
3. **The evidence-workspace change (ADR-0004) landed and green**, because the panel is composed
   into that layout.

## Kill criteria

| Criterion | Measured how | Action |
|---|---|---|
| The model asserts things the evidence does not support | ≥ 1 in 20 generated briefings rejected by the validator for an unsupported reference or number, over the five gold fixtures × four runs | Disable the LLM path; ship the template briefing only |
| It reads as a chatbot or an AI fraud detector | Any non-domain reader, after seeing the screen, describes the product that way — the criterion already standing in `01_product_decision.md` for 6 Sep | Remove the panel |
| It costs the demo its budget | p95 briefing latency > 8 s on the presentation machine, or the panel delays first paint of the reasons at all | Panel stays collapsed and on-demand; if still costly, remove |
| The template briefing is as useful as the generated one | Internal readers cannot tell them apart on the usefulness rubric in `06_evaluation_plan.md` § Workflow and usability measures | Remove the LLM; keep the template. **This is not a feature kill** — it is the same honest outcome the hybrid ML layer was built to accept |
| Anything at all reaches the risk path | The import-direction test fails | Revert the whole feature immediately; this is not negotiable and not fixable in place |
