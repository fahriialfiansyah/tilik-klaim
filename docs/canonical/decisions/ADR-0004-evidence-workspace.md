> Status: canonical — read-only once accepted. Perubahan hanya lewat ADR baru.

# ADR-0004 — `/cases/:id` becomes an Evidence Workspace

- **Status:** Proposed — awaiting owner approval
- **Date:** 2026-09-03
- **Scope:** The case detail screen (`apps/web/src/pages/case-detail/`, `apps/web/src/features/review/case-detail/`). Presentation only.
- **Owner section:** [`sprint/00-app-spec.md`](../../../sprint/00-app-spec.md) § 4
- **Supersedes:** nothing. Widgets 1–27 and display rules 1–5 all survive; three of them are re-shaped and one widget is added.

**Cross-reference (jangan salin isinya ke sini):**

- Pages, widgets, binding display rules → [`sprint/00-app-spec.md`](../../../sprint/00-app-spec.md) § 4
- Locked visual direction, four mandatory states plus the fifth for this page → [`design/DESIGN.md`](../../../design/DESIGN.md)
- What the queue and detail responses may carry → [03_architecture.md](../03_architecture.md) § Minimal API contracts
- Counter-evidence, uncertainty, and the false-accusation control → [07_privacy_threat_model.md](../07_privacy_threat_model.md)
- The 90-second and three-minute beats this screen must fit → [08_demo_runbook.md](../08_demo_runbook.md)

---

## Context

`/cases/:id` is the screen the whole product rests on: `01_product_decision.md` § 13 names the
vertical slice as *open one flagged reason → inspect claim-to-evidence links → make a human
disposition*, and `design/DESIGN.md` records that this page is "yang paling membutuhkan" the
annotation map because it carries 27 widgets and is the most expensive page to misread.

It is built and green. What it does not yet do is let a reviewer see the **shape** of the
finding in one read. Three facts are true of the screen as it stands today:

1. **The line ↔ reason ↔ evidence relationship is spread across three widgets.**
   `ClaimLineList` (widget 8–9) knows each line's support state. `ReasonCard` (widget 10–13)
   knows, per reason, which expected types were found. `EvidencePath` (widget 15) knows one
   chain for one selected line. No widget answers *"which lines does each reason touch, and
   what is missing where"* — the reviewer assembles that in their head, every case.

2. **The episode timeline is a flat list.** `EpisodeTimeline` (widget 14) sorts encounters,
   procedures and medications into one column by time. The demo's core beat (08_demo_runbook,
   25–50s) is "claim line → expected Procedure → observed missing evidence", and a single
   column cannot show an *empty lane* — which is precisely what a phantom finding looks like.

3. **The two drawers are independent of the workspace and of each other.**
   `SourceDrawer` (widget 16) and `ComparisonDrawer` (widgets 23–24) are two `Dialog`s driven
   by two unrelated `useState` hooks in the page. Selecting a different reason leaves an open
   comparison showing the previous reason's pair, and nothing structurally prevents both from
   being open at once.

Meanwhile `EvidencePath` is anchored on the **selected line**, not on the **open reason** —
so it answers "what sits under this line" when the question a reviewer is actually holding is
"what does this reason claim, and what backs or weakens it".

## Decision

Reorganise `/cases/:id` into an **Evidence Workspace**: four coordinated views over the *same*
`GET /v1/cases/{id}` response, sharing one selection.

1. **Evidence Matrix (new, widget 28).** Rows are billed lines, columns are the expected
   resource types drawn from `reason.expected_support`, cells carry one of four states.
2. **Episode Timeline becomes a swimlane (widget 14, re-shaped).** Four lanes —
   *Kunjungan*, *Tindakan*, *Obat*, *Penagihan* — over one shared time axis.
3. **Evidence Path becomes a reason-focused Evidence Map (widget 15, re-shaped).** Anchored on
   the open reason rather than the selected line, and terminating in one node per expected
   support type so the gap is visible on the map itself.
4. **One drawer host with synchronised state (widgets 16, 23, 24).** Source and comparison
   become one discriminated union in the existing Zustand store; mutual exclusion holds by
   construction, and the drawer follows the workspace selection.

**No API contract changes. No new endpoint. No DTO field added, removed, renamed, or
re-typed.** Every value the four views render already ships in `CaseDetailResponse`. The
committed contract fixtures under `apps/backend/tests/fixtures/api/` are byte-identical
afterwards, and `docs/api/openapi.json` does not move.

**No design token changes.** The workspace is composed from the semantic names already bound in
`apps/web/src/styles/app.css`; `design/tokens.css` is untouched.

### The four Matrix cell states

Four, not two, and the fourth is the one that matters:

| State | Meaning | Drawn as |
|---|---|---|
| `FOUND` | A reason citing this line cites a resource of this type, and it resolves | Neutral, openable |
| `MISSING` | A reason citing this line expects this type and cites none | Signal band, labelled *tidak ditemukan* |
| `UNRESOLVED` | A reference exists but its source availability is `MISSING` | Conflict band, labelled *rujukan tidak terselesaikan* |
| `NOT_EXPECTED` | No reason citing this line expects this type | Blank, labelled *tidak diharapkan* to assistive technology |

`NOT_EXPECTED` exists for the same reason `NOT_ASSESSABLE` is kept apart from `UNSUPPORTED`
and `NOT_STORED` from `MISSING`: an empty cell that reads as *absent evidence* manufactures a
finding the data does not make. Collapsing these four into a boolean is the failure mode this
table is designed against, and it is the same failure `07_privacy_threat_model.md` names as
"Incomplete RME looks like phantom billing".

`UNRESOLVED` is the defect state required by display rule 4 — an evidence reference that points
at nothing is a defect, not an empty panel.

## How each binding display rule survives

Display rules are quoted from `sprint/00-app-spec.md` § 4 *Aturan tampil (mengikat)*.

1. **Alasan sebelum skor.** Widget 5 stays above widget 6. The Matrix, Map and swimlane all sit
   *below* the reason rail in reading order; none of them renders a numeric score.
2. **Bukti tandingan sederajat dengan bukti pendukung.** Counter-evidence stays where it is —
   in the `ReasonCard` body, outside the collapsible. The Map draws a counter-track *in
   addition*, never *instead*. Widget 13 is not moved into a panel and is not moved into a cell.
3. **Jalur bukti kecil dan terarah — satu jalur, bukan jaring hubungan.** This is the rule the
   Evidence Map is most likely to be accused of breaking, so the compliance argument is stated
   rather than assumed: the Map keeps **exactly one trunk** — claim → cited line → encounter —
   and the expected support types hang off the trunk's last node as **terminals**, which have no
   successors and never link to each other. Terminals fan out; they do not interconnect. The
   graph is a tree of depth ≤ 4 with a single path to every node, which is what "one path" means
   operationally. If any future change gives a node two parents, or links two terminals, the
   rule is broken and the change is wrong.
4. **Rujukan bukti wajib dapat dibuka.** Every reference in the Matrix, the Map and the swimlane
   opens through the same `EvidenceRefButton` → source-index resolution used today, and an
   unresolvable reference renders as `UNRESOLVED`, never as a blank.
5. **Seluruh alur dapat diselesaikan dengan papan ketik.** The Matrix is a real `<table>` with
   `<th scope>` and focusable cells; the swimlane keeps its ordered-list semantics per lane; the
   unified drawer host keeps Radix focus trapping, Escape-to-close, and explicit focus return to
   the element that opened it — the app uses no `DialogTrigger`, so restoration stays manual.

Additionally, from `design/DESIGN.md`: every state carries a **text label, never colour alone**,
and the page keeps its five mandatory states — memuat, kosong, galat, nonaktif, and *versi
usang*.

## What is deliberately not done

- **The timeline payload is not extended.** A *Dokumen* lane and a *Penagihan* lane sourced from
  the backend would each need new `TimelineEvent` entries, which changes a committed contract
  fixture for a presentational gain. The *Penagihan* lane is therefore derived in the client
  from `detail.lines[].service_at`, which is already on the wire. A *Dokumen* lane is left out
  entirely rather than reconstructed by parsing `SourceField` values — a lane built from parsed
  display strings is a lane that breaks silently.
- **No graph library.** Cytoscape.js is listed in `03_architecture.md` as "only if useful"; a
  depth-4 tree with a single trunk is not a use for it. The Map is laid out with CSS.
- **No new state persisted.** Workspace selection is ephemeral. The disposition draft in
  `store.ts` keeps its current lifetime, because a refused save must still re-render with the
  reviewer's input intact.

## Consequences

- The reviewer's core question — *which billed lines lack which evidence* — is answerable from
  one widget instead of three, and the answer is the same one the reason cards and the request-
  evidence checklist give, because all three read the same two DTO fields.
- The empty lane in the swimlane is the phantom finding made visual; the demo's 25–50s beat
  gains a picture it currently narrates.
- The drawer can no longer disagree with the workspace, and two drawers can no longer stack,
  because the state that would allow it is unrepresentable.
- **Reverting is a frontend-only revert.** No migration, no contract change, no regenerated
  artifact. That is what makes the kill criteria below cheap enough to honour.
- `sprint/00-app-spec.md` § 4 gains widget 28 and re-shapes the descriptions of widgets 14 and
  15. The spec, not this ADR, remains the widget authority.

## Kill criteria

Pre-committed, measurable, and each one reverts a named piece rather than the whole change.

| Criterion | Evidence of failure | Action |
|---|---|---|
| The Matrix does not make the finding faster to read | Three non-domain readers cannot answer *"which line is missing what?"* within 30 seconds of opening a seeded phantom case | Remove widget 28; widgets 8–13 stand as today |
| The Map reads as a network | A reviewer describes widget 15 as a graph, web, or network, or any node acquires two parents | Revert widget 15 to today's single-track `EvidencePath` |
| The workspace costs the demo its beat | The 25–50s evidence beat of the 90-second flow overruns on the presentation machine | Revert the whole workspace; the current screen is the fallback |
| The swimlane hides the sequence it was meant to show | A four-lane layout pushes a normal episode below the fold at 1440×900 | Fall back to widget 14 as it is today |

A revert here is a designed outcome, not a failure, and it costs one `git revert` of a
frontend-only commit range.
