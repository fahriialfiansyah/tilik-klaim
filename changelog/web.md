# Changelog — Web

Append-only. Newest entry at the top.

---

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
