# Changelog — Web

Append-only. Newest entry at the top.

---

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
