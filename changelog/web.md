# Changelog — Web

Append-only. Newest entry at the top.

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
