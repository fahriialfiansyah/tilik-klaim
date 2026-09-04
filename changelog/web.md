# Changelog — Web

Append-only. Newest entry at the top.

---

### 2026-09-04 · Shell polish: a real logout dialog, icon-only theme switch, drawn menu marks · ✅ Done

**Event:** Four owner requests on the shell, and one of them removed a control that was too cheap for what it did
**Files:** `src/components/layouts/{AppHeader,AppSidebar,MenuIcons}.tsx`, `src/modules/theme/ThemeToggle.tsx`, `src/features/auth/components/ProfileMenu.tsx`, `tests/e2e/auth-roles.spec.ts`
> **The profile control moves to the far right**, where an account control is looked for — but
> *after* the `DATA SINTETIK` badge, not before it. The badge is a governance statement about the
> data and must not be pushed to the edge where a reader stops scanning.
> **Signing out now asks.** It ends the session *and* empties whatever the reviewer had in
> progress, and neither is undoable — a menu item doing both on one click is a menu item next to
> which a mis-click is expensive. The dialog changes its own wording when a draft is unsaved, so
> the draft case names what is about to be lost instead of repeating the generic question.
> **The dialog content is rendered unconditionally inside `Dialog`.** Putting it behind a second
> `{open ? … : null}` is the trap `lib/useLastPresent.ts` exists for: the content is torn out in
> the same commit that flips `open`, Radix's close cleanup never runs, and focus lands on
> `<body>`. This dialog has no payload to keep alive, so it simply stays mounted.
> The corner X keeps its default name *Tutup* while the footer button is *Batal* — two controls
> sharing one accessible name are two controls a screen reader cannot tell apart.
> **The theme switch is a sun and a moon, drawn here** rather than imported, so the stroke weight
> matches the product mark. The word beside it is gone from the surface but **not** from the
> accessible name: `aria-pressed` carries the state and `aria-label` names the act, because a
> control whose meaning lives only in a picture is one a screen reader cannot describe.
> **Each menu entry gets its own mark.** The three uneven bars that used to sit there were the
> same shape on every entry — decoration, not a signpost. Now: a work list with the queue's own
> priority rail; a bundle arriving in a tray; three measured bars on a baseline, because a bar
> without an axis is a shape rather than a measurement; and two people with a role band for the
> roster. All `aria-hidden` — the label beside each carries the meaning, and an icon repeating it
> would make every entry announce itself twice.
> Verified: web **241** passed (was 239) · playwright **41** passed (was 40) · tsc clean.

### 2026-09-04 · The login page *is* the access matrix (Sprint 10, ADR-0006) · ✅ Done

**Event:** `analis casemix` is gone; `/login` teaches the role model before anyone signs in, and a favicon finally exists
**Files:** `src/features/auth/**`, `src/features/admin/users/**`, `src/pages/{login,admin-users}/*`, `src/config/menu/app-menu.ts`, `src/App.tsx`, `src/lib/http.ts`, `src/components/layouts/{AppHeader,AppSidebar}.tsx`, `src/components/ui/{button,dropdown-menu}.tsx`, `src/components/brand/TilikKlaimMark.tsx`, `src/assets/favicon.svg`, `rsbuild.config.ts`, `apps/backend/scripts/export_access_matrix.py`
> **The first design was rejected, correctly.** It was a brand panel on the left and a form on
> the right — the layout every dashboard ships — and it scrolled, because three account cards
> stacked under the form made the page ~1.240 px tall at 1440×900. The first thing a judge would
> have seen was a login that does not fit on screen.
> **What shipped instead: the page is the ADR-0006 § 2 access matrix.** Rows are the three
> synthetic staff, columns are what each may do, and choosing a row chooses who signs in. Anyone
> reading it learns in five seconds that there are three roles and that the administrator touches
> no claim — which is the separation of duties `07_privacy_threat_model.md` names, made visible
> rather than described. It also settles the "Role/access matrix" that § Governance deliverables
> had listed as owed: it is now a live artefact instead of a table in a document.
> **The matrix is generated, not retyped.** `scripts/export_access_matrix.py` writes
> `access-matrix.json` from `app/service/access.py`, and
> `test_the_exported_access_matrix_matches_the_server` fails when the committed file drifts —
> the same discipline the demo samples already follow. It matters more here than anywhere else:
> a hand-maintained copy would be a screen that quietly lies about what the server permits.
> `matrix.test.ts` additionally asserts every displayed column exists in the generated file, so a
> column can never be invented in the UI.
> **Selection is a real radio group inside a real table.** Arrow keys walk the personas, the group
> has one tab stop, and assistive technology announces the person and the column heading together.
> A `<div role="radio">` would have given none of that for free.
> **Colour never carries the answer.** Every cell says *Boleh* or *Tidak* in words; tick and cross
> are `aria-hidden`.
> **The background is generated from the product's own data shape** — claim lines, evidence
> connectors, and rare amber gaps — at 24% opacity, clipped below the header band. The first
> attempt ran over the navy band and read as dirt rather than texture. It carries no organisation's
> marks: the competition's originality rule forbids using intellectual property that is not ours
> (`00_competition_brief.md` § Eligibility, [PDF-PG pp. 4–5]), and the submission checklist wants
> visual licences documented — a background this file draws answers that line in a sentence.
> **The footer states the context and the limit**: Healthkathon 2026, Kategori 2, and *"bukan
> produk atau layanan resmi BPJS Kesehatan"*. The disclaimer is the same stance that makes the
> rest of the proposal credible.
> **`h-svh` + `overflow-hidden`, and a Playwright spec asserts the page does not scroll** at
> 1440×900 — measured, not promised.
> **The profile menu replaces the hardcoded role constant.** Radix `DropdownMenu`, so focus,
> Escape and click-outside are its. Unlike `dialog.tsx` it needs **no** manual focus return: that
> file restores by hand because every drawer opens from an ordinary button and Radix's restore
> aims at a `DialogTrigger` this app never uses — a dropdown always has one.
> **Signing out warns when a disposition draft is unsaved.** `store.ts` keeps drafts alive so a
> refused save costs the reviewer nothing; a sign-out that silently discarded one would undo that
> guarantee from the other direction. `evidenceSeeded` deliberately does not count — that is the
> system's pre-tick, not the reviewer's work.
> **Navigation is role-aware from `src/config/menu/app-menu.ts` and nowhere else.** An
> administrator's sidebar has one entry — thin on purpose, and the point. Hiding a link is a
> courtesy; two Playwright specs check the API directly with a forged header so the UI and the
> server cannot silently disagree.
> **`ACTOR_ROLE = 'reviewer'` is deleted.** `X-Actor-Role` and a new `X-Actor-Id` now come from
> the session, attached once in `src/lib/http.ts`.
> **`/admin/users`** is a real `<table>` with `<th scope>`, bounded through `PerfectScrollArea`,
> four states, and an append-only trail beneath it. The signed-in admin's own row is disabled
> **and says why** rather than sitting greyed out.
> **`Button` gained `forwardRef`** and `TilikKlaimMark` gained `onSurface` — its solid stroke is
> `--t-inv`, which is near-white and invisible on the page surface the mark now sits on.
> **A favicon exists at last — and its first version never rendered.** It explained itself in an
> XML comment that named design tokens (`--t-inv`, `--logo-amb`); a double hyphen is illegal
> inside an XML comment, so the file was unparseable and every browser fell back to its default
> globe. Nothing failed: the build succeeded, the `<link rel="icon">` was present and correct, and
> the tab looked *almost* right. Found by the owner looking at their own tab strip — the same way
> every hard defect in this project has been found.
> The notes now live in `<title>`/`<desc>`, and `favicon.test.ts` parses the file and refuses both
> XML comments and `var(--…)`: a favicon is the one asset nothing else in the app renders, so
> nothing else fails when it breaks.
> **It was also redrawn for the size it is actually read at.** The full mark on navy resolved as a
> smudge at 16 px, and a dark plate has nothing to sit against on a dark tab strip. It is now a
> bold ring with a gap and one amber node on a white plate — the same idea, reduced rather than
> shrunk, and legible on both a light and a dark chrome.
> Verified: web **239** passed (was 184) · playwright **40** passed (was 24) · tsc clean.

### 2026-09-04 · The briefing panel, driven by a real model · ✅ Done

**Event:** First run of the panel against the live vLLM gateway rather than a fake provider
**Files:** `tests/e2e/case-briefing.spec.ts`, `playwright.config.ts`
> The panel needed no change — the streaming progress log, the kind chips, the openable
> references and the provenance line all worked first time against a real model. Screenshot:
> `docs/qa/2026-09-03-case-briefing/06-model-briefing-vllm.png`.
> **Two test-only corrections.** The spec asserted "Templat deterministik", which fails on any
> machine where the gateway *is* configured — reporting a working feature as broken. It now
> asserts the guarantees that hold on both paths: provenance is stated, every observation carries
> an openable reference, nothing accusatory appears. And the suite's 7-second assertion timeout is
> right for a rendered page and wrong for a model, so the briefing assertions carry their own.
> Verified: web 184 · tsc clean · playwright **24 passed**, briefing specs against the live model.

### 2026-09-03 · "Ringkasan bukti" — the briefing panel (Sprint 09, ADR-0005) · ✅ Done

**Event:** Collapsed, on-demand, non-authoritative panel at the bottom of the middle column
**Files:** `src/features/review/case-briefing/**`, `src/pages/case-detail/CaseDetailPage.tsx`, `src/env.d.ts`, `tests/e2e/case-briefing.spec.ts`
> Named for what it is, never for how it is made: no "agent", "AI", or "assistant" anywhere a
> reviewer reads, because `01_product_decision.md` makes "readers call it an AI fraud detector /
> chatbot" a kill criterion. Provenance ("Templat deterministik" · model id · prompt version) is
> stated *after* the observations, questions and uncertainty note.
> **Never volunteers.** Collapsed on mount; nothing is fetched until "Susun ringkasan" is
> pressed (asserted with a `fetch` spy, and end-to-end with a request listener). Last in DOM
> order after the swimlane (asserted with `compareDocumentPosition`).
> **No path to the decision.** No action control, radio or checkbox; the feature imports nothing
> from `case-detail/store` — asserted on the source via `?raw` imports, the frontend twin of the
> backend's syntax-tree guard. End-to-end: a half-filled disposition survives a briefing run.
> **Streaming via `fetch` + reader** on the relative `/v1` base, parsed by a pure frame parser
> (`parseSseChunk`) and applied by a pure reducer (`applyEvent`), both unit-tested. If the stream
> ends without a terminal event or fails, the `?stream=false` answer is fetched and the panel says
> "dimuat tanpa aliran". Through the Rsbuild dev proxy the stream arrived intact — the e2e spec
> asserts the fallback marker is *absent* — so risk #3 in the plan did not materialise.
> Verified: web **184 passed** (was 168) · tsc clean · playwright **24 passed** (was 21) in 20.0 s.
> Screenshots: `docs/qa/2026-09-03-case-briefing/` (five frames, both themes).

### 2026-09-03 · `/cases/:id` becomes an Evidence Workspace (Sprint 08, ADR-0004) · ✅ Done

**Event:** Four coordinated views over one selection; no API, DTO, token, or contract-fixture change
**Files:** `src/features/review/case-detail/{store,matrix,swimlanes,map}.ts` (+tests), `components/{EvidenceMatrix,EpisodeSwimlane,EvidenceMap,CaseDrawerHost}.tsx` (+tests), `components/{EvidencePath,EpisodeTimeline}.tsx` **deleted**, `labels.ts`, `src/pages/case-detail/CaseDetailPage.tsx`, `tests/e2e/evidence-workspace.spec.ts`, `sprint/00-app-spec.md` § 4
> **Evidence Matrix (widget 28).** Lines × expected resource types, derived entirely from
> `CaseDetailResponse`. Four cell states, each with words: `ditemukan`, `tidak ditemukan`,
> `rujukan tidak terselesaikan` (display rule 4's defect), and `tidak diharapkan` — the one that
> matters, because an empty cell that read as *absent* would manufacture a finding. Reasons that
> cite no line (repeat, clone, unbundling) get a *Tingkat klaim* row instead of vanishing.
> **Swimlane (widget 14).** Four lanes on one shared minute axis; the *Penagihan* lane is derived
> in the client from `lines[].service_at`. An empty lane is drawn and says so.
> **Evidence Map (widget 15).** Anchored on the open reason: one trunk (claim → cited line),
> terminals per expected type and per cited reference, counter-evidence on a labelled dashed
> branch *in addition to* the reason card. `assertSinglePath` fails in dev if a node ever gains two
> parents — display rule 3 made mechanical.
> **One drawer host.** Source and comparison are one discriminated union in the store, so "both
> open" is unrepresentable. Selecting a different reason or line closes the drawer. Drafts are
> untouched by every workspace action, asserted.
> **Found by looking, not by tests:** the billing lane flagged un-cited line 89.7 as *cacat
> integritas bukti* — the API indexes sources only for cited resources, so a client-derived
> reference to an un-cited line is not a defect and now carries no reference. Noted in passing:
> `case-detail-a11y.spec.ts`'s `toHaveCount(0)` on broken refs resolves before the detail
> loads, so it would not have caught this; worth a `waitFor` on the matrix in a later pass.
> Verified: web **168 passed** (was 107) · tsc clean · playwright **21 passed** (was 17) in 16.4 s ·
> backend 338 · domain 23 · data 57 · model 71 · evaluation 47 — all unchanged.
> Screenshots: `docs/qa/2026-09-03-evidence-workspace/` (13 frames, both themes, five states).

### 2026-09-01 · [Sprint 04 — review-slice](../sprint/backlog/04-review-slice/sprint.md) · Task: [Ingest and seeded demo page](../sprint/backlog/04-review-slice/frontend/03-ingest-page.md) · ✅ Done

**Event:** Task completed — sprint 04 frontend is finished
**Files:** `apps/web/src/features/review/ingest/`, `apps/web/src/pages/ingest/`, `apps/web/public/samples/`, `apps/web/src/lib/http.ts`, `apps/web/tests/e2e/ingest.spec.ts`
> Widgets 1–11: a drop zone with its limits stated up front, the five curated scenarios, the
> validation report, the error table, the input hash, and exactly one button.
>
> **The absence of a configuration wizard is the feature.** No detector picker, no threshold, no
> mode — not in the UI, and not in `ScreenRequest` either, which is what makes it enforceable
> rather than a promise. A presenter who could tune the engine between two runs could tune their
> way to a result, and the demo would prove nothing.
>
> **The five samples are generated from the backend's gold fixtures**, not copied by hand:
> `apps/backend/scripts/export_demo_samples.py` writes them to `public/samples/`, and
> `tests/test_demo_samples.py` fails if they drift, if a sample loses the history its
> cross-claim rules need, or if a fixture's **answer key** ever reaches the browser. The
> expected reason codes live outside `CanonicalBundle` precisely so no detector can see them;
> shipping them to a demo audience would undo that.
>
> Static files rather than an endpoint, for two reasons: `docs/canonical/08_demo_runbook.md`
> needs the demo to run with no external network, and sprint 07 owns the demo/reset route — a
> new endpoint here would pre-empt a design that sprint has not made yet.
>
> **Three scenarios carry a prior claim, and the rows say so.** Repeat billing, cloned
> documentation, and unbundling are only visible *across* claims, so those samples submit their
> history first. Ingesting two bundles while appearing to ingest one would misrepresent how the
> detector works.
>
> **The defect worth recording: a rejected bundle is not a broken service.** The API refuses a
> bundle along two different paths — a `4xx` envelope for anything caught before parsing
> (oversized, malformed, too deep) and a `200` report with `status: INVALID` for anything caught
> after. A plain `catch` renders the first as "the request failed" and offers a retry, on a file
> that will be refused identically every time, while hiding the stable code the operator needs
> to fix it. `ApiError` now carries the server's `issues`, and `rejection.ts` maps all three
> refusal sources — browser limit, pre-parse `4xx`, post-parse `INVALID` — onto one status the
> screen can render.
>
> The screen button stays in place when a bundle is refused, disabled with the reason, rather
> than disappearing: widget 9 specifies "nonaktif disertai alasan", and a control that vanishes
> leaves the operator hunting for it instead of reading why.
>
> Seven Playwright specs against the real API, including the identical-bundle path (pressing
> screen twice must not put twin cases in the queue) and the oversized file (asserted by
> counting network requests, which must be zero).

---

### 2026-09-01 · [Sprint 04 — review-slice](../sprint/backlog/04-review-slice/sprint.md) · Task: [Case detail, evidence trace, and disposition panel](../sprint/backlog/04-review-slice/frontend/02-detail-kasus.md) · ✅ Done

**Event:** Task completed
**Files:** `apps/web/src/features/review/case-detail/`, `apps/web/src/pages/case-detail/`, `apps/web/src/components/ui/dialog.tsx`, `apps/web/src/lib/useLastPresent.ts`, `apps/web/tests/e2e/`, `apps/web/playwright.config.ts`
> Widgets 1–27 on one screen, built against the live seeded API. The density is the point: the
> workflow's contract is **one screen to resolve one reason**, and a reviewer who has to
> navigate away to weigh counter-evidence will decide without it.
>
> All five binding display rules are implemented and each is asserted somewhere:
>
> * **Reason before score.** The reason sentence is the page's `<h1>`; the band and the
>   confidence basis sit below it in DOM order as well as visually.
> * **Counter-evidence has equal standing.** Widget 13 renders *outside* the reason card's
>   collapsible, so collapsing a card does not hide the argument against it. When a reason has
>   none the section says so rather than vanishing — an absent heading reads as "nothing was
>   looked for", not "nothing was found".
> * **One evidence path, not a network.** Claim → line → visit → clinical evidence, stopping at
>   the first node with nothing under it. Every node has at most one successor by construction.
> * **Every reference opens.** Each one resolves against the source index the API now ships, and
>   an unresolvable one renders as a flagged **evidence-integrity defect** rather than a link
>   that does nothing.
> * **Keyboard-operable throughout,** proven by a Playwright spec rather than by inspection.
>
> **Playwright installed** (pre-authorised) with the three specs the task names plus an
> accessibility smoke — seven tests, run against the real API and a seeded database because two
> of them assert something only a real server can refuse. The whole suite finishes in about
> seven seconds, which also settles the task's under-90-seconds demo assertion.
>
> **Four defects found by opening the page, not by the compiler:**
>
> 1. **Focus never came back from a drawer.** Radix restores focus to `DialogTrigger`, which
>    this app does not use — every drawer opens from an ordinary evidence-reference button — so
>    the ref was null, Radix's `preventDefault()` suppressed the browser's own restore, and
>    focus landed on `<body>`. With a mouse it is invisible; with a keyboard every closed drawer
>    sent the reviewer back to the top of the page. `Dialog` now captures the previously focused
>    element during render (a parent's effects run *after* its children's, by which time the
>    focus scope has already moved focus) and restores it on close.
> 2. **Hovering an action looked identical to selecting one.** Both drew the brand border and
>    tinted ground, so running the pointer down the four actions made each look chosen in turn.
>    Hover now only firms the border.
> 3. **The evidence path accused a case with nothing wrong with it.** The chain always ended in
>    a "bukti klinis tidak ditemukan" node, including on a case where no detector had fired and
>    every line was supported. With no reason selected the path now simply stops.
> 4. **Form controls were drawn as stand-ins beside a visually hidden input.** The control was
>    no longer where it appeared to be, so a click landed on the label and hit-testing missed it
>    entirely. Radios and checkboxes are now styled in place with `appearance-none`.
>
> The disposition draft lives in a module store rather than component state, and that is the
> screen's central guarantee rather than a structural preference: a stale-version rejection
> re-fetches the case and re-renders the panel, and component state would come back empty. The
> reviewer's action, reason, and note survive both a refused save and a failed one, and the
> banner names what changed, who changed it, and offers a reload.

---

### 2026-09-01 · [Sprint 04 — review-slice](../sprint/backlog/04-review-slice/sprint.md) · Task: [Review queue page](../sprint/backlog/04-review-slice/frontend/01-antrean-review.md) · ✅ Done

**Event:** Task completed
**Files:** `apps/web/src/features/review/{queue,shared}/`, `apps/web/src/pages/queue/`, `apps/web/src/lib/http.ts`, `apps/web/rsbuild.config.ts`
> The operator's home screen, built against the **live seeded API** rather than fixtures —
> the endpoints were already complete, so every row on screen is a real response.
>
> Five metric cards, each clickable into its own filter. Filters for status, mode, band, and a
> date range, all server-side and combinable, each showing as an individually removable chip.
> Four sort keys, also server-side. Column order is binding and tested: the working-language
> reason sentence is the first column, ahead of any score, band, or amount.
>
> All four empty and error states are distinct, which `brief/03` § 4.3 calls the most damaging
> defect to get wrong here. Verified by stopping the API: the failure state says the list did
> not arrive, and never poses as "no cases".
>
> **One defect caught in the browser, not by the compiler:** the evidence meter drew three
> filled segments when `total_lines` was 0, so a case the screening never assessed rendered
> identically to one with complete support. Now three outcomes stay apart — incomplete bundle,
> nothing to assess, and n-of-m supported — and none of them is ever green.
>
> Rows carry one tab stop each, a real link, rather than a `tabIndex` on the `<tr>`.
>
> **Two defects found by measuring the rendered page rather than trusting the tokens:**
> `tailwind-merge` was silently dropping the text colour from every Button — it only knows
> Tailwind's stock type scale, so it read `text-body-lg` as a *colour*, judged it to conflict
> with `text-brand-on`, and kept the last one; the primary button rendered near-black on dark
> teal at **2.5:1**. `cn()` now declares the project's type scale, and a regression test covers
> it. Separately, `--t-3` was corrected again (`#6b7977` → `#63706e`): the August fix measured
> it only against `--s-card`, but the app also paints it on `--s-sunk` (4.33:1) and `--s-page`
> (4.07:1). Every status indicator, label, and button on `/` now clears AA in both themes;
> lowest is 4.63:1.
>
> **Code review of this change found three more, all fixed:** search moved server-side (it was
> filtering one already-paginated page, stranding matches on later pages behind an empty state
> that offered only "clear the filters"); the band column no longer reports an `aria-sort`
> direction that flips while the rows sit still, since the server refuses to invert that sort;
> and the band's rationale — the sentence that keeps "Tidak ada risiko teramati" from reading as
> a verdict — is now announced to screen readers instead of living only in a `title` no keyboard
> can reach. One test was wrong rather than the code: asserting the words "bersih"/"aman" never
> appear flagged the sentence that *denies* them, so it now asserts on the phrase.
>
> Verified: 18 web tests, tsc clean, 285 backend tests, build 551 kB (359 kB gzip).

### 2026-09-01 · [Sprint 04 — review-slice](../sprint/backlog/04-review-slice/sprint.md) · Task: [Port design tokens](../sprint/backlog/04-review-slice/frontend/00-port-design-tokens.md) · ✅ Done

**Event:** Task completed — **toolchain unblocked**, Tailwind v4 + shadcn/ui
**Files:** `apps/web/src/styles/`, `apps/web/postcss.config.mjs`, `apps/web/components.json`, `apps/web/src/components/{ui,layouts,wrappers,brand}/`, `apps/web/src/modules/`
> Tailwind v4 is CSS-first, so there is no `tailwind.config.ts`: the theme is a `@theme` block
> in `src/styles/app.css`. It uses `@theme inline`, which emits `var(--token)` into the
> utilities instead of a resolved value — that is what lets the `[data-theme]` switch repaint
> both themes without a rebuild. `src/styles/tokens.css` is a literal `cp` of
> `design/tokens.css`, verified byte-for-byte, so resyncing stays mechanical.
>
> **Tailwind's default colour palette is deleted** (`--color-*: initial`). `design/DESIGN.md`
> reserves red for deterministic conflict and green for completed, validated actions; while
> `bg-red-500` still existed that rule could only be enforced by review. It now produces
> nothing, so misuse surfaces where it is typed rather than in front of judges. shadcn's
> `destructive` Button variant was dropped for the same reason — this app has no destructive
> action for red to mean.
>
> Fonts are self-hosted via `@fontsource`, not the mockup's Google Fonts link: `brief/03`
> § 9.3 requires full function with no external network and the demo runbook is offline.
> Latin subsets only — shipping all of them cost 675 kB for scripts this app never renders.
>
> Two namespace collisions found and fixed by reading the emitted CSS: `--color-page` claimed
> the `text-page` utility from the 30 px font size, and `--shadow-card` would have collided
> with `--color-card`. Micro-labels raised 9 px → 11 px by owner decision, applied at source.

### 2026-08-30 · [Sprint 00 — foundation](../sprint/backlog/00-foundation/sprint.md) · Task: [App shell](../sprint/backlog/00-foundation/frontend/01-app-shell.md) · ✅ Done

**Event:** Task completed
**Files:** `apps/web/`
> React 18 + TypeScript + Rsbuild. Navigation driven by `src/config/menu/app-menu.ts` per the
> architecture rules; shell regions each reserve layout space. Four routes wired from
> `sprint/00-app-spec.md`. Verified: typecheck clean, build 165.6 kB (55.0 kB gzip).

### 2026-08-30 · Sprints 04, 06, 07 · 📋 Added

**Event:** Task created (6 frontend tasks)
**Files:** `sprint/backlog/{04,06,07}-*/frontend/*.md`
> Sprint 04: `00-port-design-tokens` (⏸ blocked on the design team), queue, case detail,
> ingest. Sprint 06: evaluation page. Sprint 07: 90-second demo rehearsal.

### 2026-08-30 · [Sprint 04 — review-slice](../sprint/backlog/04-review-slice/sprint.md) · Task: [Port design tokens](../sprint/backlog/04-review-slice/frontend/00-port-design-tokens.md) · 🔓 Unblocked

**Event:** Design blocker cleared
**Files:** `design/tokens.css`, `design/mockup/`, `design/DESIGN.md`, `design/flow.json`
> Design team delivered a Claude Design canvas bundle covering all four screens. Unpacked into
> `design/mockup/reference.html` (readable markup — the bundle itself is one 405 kB base64
> line) with `unpack.py` so the next revision resyncs mechanically instead of by hand.
> `design/tokens.css` holds 35 colour tokens across light and dark, plus type scale, spacing,
> radius, and semantic band aliases that encode the binding colour rules: red only for
> deterministic conflict, green only for completed and validated actions.
> Contrast measured: all five status bands clear AA in both themes (lowest 5.81:1 light,
> 7.50:1 dark). Two deviations recorded rather than silently resolved — body text is 13 px
> against a locked 14–16 px, and `--t-3` reaches only 4.41:1. Remaining work is the Tailwind
> and shadcn install, which waits on an explicit go-ahead.

### 2026-09-01 · [Sprint 06 — evaluation-report](../sprint/backlog/06-evaluation-report/sprint.md) · Frontend: [evaluation page](../sprint/backlog/06-evaluation-report/frontend/01-evaluation-page.md) · ✅ Done

**Event:** `/evaluation` is live — the fourth and last screen, reading artifacts only
**Files:** `src/features/review/evaluation/**`, `src/pages/evaluation/EvaluationPage.tsx`
> All nine widgets render from `GET /v1/evaluations/latest`. **Display only**: the single button
> on the page is *Salin* on the limitations card. A page that could re-tune a threshold would let
> someone tune against the frozen test set it is showing.
> **Charts and tables cannot disagree by construction** — both are built by one selector from one
> response and rendered through one formatter, so a mismatch could not be a rounding difference.
> **All four baselines and all four modes are always listed**, in canonical order, whether or not
> the response carries them. A missing row reads *tidak terukur*; iterating the response instead
> would make an unmeasured baseline silently vanish from the comparison.
> **`absent` is a distinct status from `failed`.** "Nothing has been run" shows the command;
> "the service is down" shows a retry. Both produce an empty page and mean opposite things.
> **Three defects found only by opening the page**, all of which passed the compiler, 104 unit
> tests, and a read-through: case counts rendered as `7.0000` because every cell went through one
> metric formatter; the limitations card rendered in English on an Indonesian screen, because the
> canonical rows are English and the artifact carries them verbatim; and the manifest's English
> `threshold_logic` string printed raw into the version card. Click-through and screenshots in
> `docs/qa/MANUAL-QA.md` § 1d.
> **Widget 6 deviates from the spec and it is flagged.** § 6 asks for precision across *various*
> budget sizes; the frozen `EvaluationResponse` carries one fixed budget and has no field for a
> curve, so the page compares the four baselines at that budget. The sweep needs a wire-model
> change, which was not taken unilaterally.
> Verified: web 104 passed (was 91) · tsc clean · playwright 14 passed in 10.0s.

### 2026-09-01 · [Sprint 07 — demo-hardening](../sprint/backlog/07-demo-hardening/sprint.md) · Frontend: [demo flow & fallback](../sprint/backlog/07-demo-hardening/frontend/01-demo-flow-rehearsal.md) · 🚧 In Progress

**Event:** The 90-second flow is walked, timed, and proven offline; the human rehearsal is owed
**Files:** `apps/web/tests/e2e/demo-flow.spec.ts`, `docs/artifacts/screenshots/`
> Three tests, ~3.5 s: the full path timed against a budget, the evaluation beat inside its
> twenty-second slot, and every demo route walked with **every non-localhost request aborted** —
> offline verified by blocking the network, not by assuming it. Suite is now 17.
> **The budget is asserted, not assumed.** A flow that works but takes two minutes fails on stage
> as surely as one that errors. The machine finishes in ~3.5 s and the test holds it under 30 s,
> leaving two thirds of the runbook's ninety for narration. Passing is necessary, not sufficient:
> the machine does not narrate or move a cursor.
> **The spec resets itself** via `scripts/demo_reset.py` in `beforeAll`, because requesting
> evidence moves the demo case out of the state the flow starts from — so a second run would find
> it already dispositioned, which is the exact failure the reset exists to prevent.
> **Two behaviours the runbook does not describe, found by walking it.** Requesting evidence hands
> the reviewer to `/ingest?case=…` rather than back to the queue — right, since that is where the
> facility's replacement bundle arrives, and a better beat than the runbook's. And the audit
> timeline reads in working language, so the test asserts *Disposisi dicatat* rather than the raw
> `DISPOSITION` enum; `OPENED` once shipped untranslated into an otherwise Indonesian history.
> Four proposal artifacts captured to `docs/artifacts/screenshots/`; the capture asserts on every
> page that the synthetic badge is present and that nothing matching a 13- or 16-digit identifier
> or `NIK` appears — checked rather than eyeballed.
> **Still owed, and human:** the three-minute rehearsal with narration, two written case studies,
> the recorded 1080p fallback, and the six-frame screenshot PDF.
> Verified: web 104 passed · tsc clean · playwright 17 passed in 12.6 s.

### 2026-09-01 · Comparison drawer: a route to the candidate · ✅ Done

**Event:** The drawer named a candidate claim and offered no way to open it
**Files:** `src/features/review/case-detail/components/ComparisonDrawer.{tsx,test.tsx}`
> `candidate_case_id` arrived on the wire and was never rendered, so a reviewer comparing two
> claims had to return to the queue and find the second one by hand — on the screen this project
> treats as the most expensive to misread. The drawer now names the candidate claim and, when a
> case exists, links to it.
> **Two null cases read as "nothing to open", not as a dead link**, because neither is a defect:
> a candidate accepted but never screened has no case, and a clone candidate is another
> participant's note, which cloning compares across and the service receives without the
> submission behind it. Both are asserted in `ComparisonDrawer.test.tsx`.
> Verified: web 107 passed (was 104) · tsc clean · playwright 17.

### 2026-09-01 · Router advisory audited; one navigation site hardened · ✅ Done

**Event:** `react-router-dom` 6.30.6 carries two moderate advisories; neither is exploitable here
**Files:** `src/features/review/ingest/components/IngestBanners.tsx`, `docs/artifacts/router-advisory-audit.md`
> The SSR `deserializeErrors` advisory does not apply: this app is a static client bundle with no
> server render and no hydration. The open-redirect advisory needs attacker-controlled input to
> reach a navigation target **as a path prefix**; every target here is either a literal or a
> server-generated identifier. Full table in the audit.
> **One site took raw user input.** `IngestBanners` navigates to `/cases/${caseId}` where `caseId`
> comes from the `?case=` query string. Still not exploitable — the literal `/cases/` prefix means
> the path can never *begin* with `\\` or `//` and so can never become protocol-relative — but it
> now uses `encodeURIComponent`, matching what `CaseDetailPage` already did. One line, removes the
> only vector, and stops the argument depending on router normalisation behaviour that could
> change between versions.
> **Recommendation: do not upgrade to v7 before G8.** It is breaking, it fixes nothing real here,
> and it touches every route in the app days from a deadline. "Audited, does not apply, here is
> why" beats a list quietly ignored.
