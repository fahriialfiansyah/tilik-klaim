# Task 00 — Port design tokens and wire Tailwind

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** no — one-time styling setup. Go-ahead given 31 Agu: Tailwind v4 + shadcn/ui.

> **Unblocked on 30 Aug.** The design team delivered
> [`design/mockup/tilik-klaim-v2.bundle.html`](../../../../design/mockup/tilik-klaim-v2.bundle.html);
> [`design/tokens.css`](../../../../design/tokens.css) now holds 35 colour tokens across a light
> and a dark theme, plus type scale, spacing, radius, and semantic band aliases. Contrast was
> measured: all five status bands clear AA in both themes.
>
> What remains is the toolchain step — installing Tailwind and shadcn/ui and binding them to
> those tokens. That is a dependency change, so it waits on an explicit go-ahead rather than
> being taken autonomously. Two design questions are still open; see
> [`design/DESIGN.md`](../../../../design/DESIGN.md) § Deviasi.

## Goal

Bind the design system's tokens to the app so components render in the agreed visual
language instead of browser defaults.

## Files to touch

- `apps/web/package.json` — add Tailwind and shadcn/ui
- `apps/web/src/styles/tokens.css` — values ported from `design/tokens.css`
- `apps/web/src/styles/components.css` — scrollbar theming per the design tokens
- `apps/web/tailwind.config.ts` — bind Tailwind theme to the tokens

## Skills to consult

- `design/DESIGN.md` — the locked direction
- `.claude/rules/architecture.md` § Web UI Enforcement — shadcn binding and scroll regions

## TODOs

- [x] Obtain the design tokens — delivered as `design/tokens.css`, extracted from the team's mockup
- [x] Install and configure Tailwind — v4, CSS-first. There is no `tailwind.config.ts`; the theme lives in `@theme` in `src/styles/app.css`
- [x] Port tokens into `src/styles/tokens.css` — a literal `cp`, verified byte-for-byte against the source
- [x] Bind the Tailwind theme to the tokens — `@theme inline`, so utilities read the token at runtime and `[data-theme]` switching needs no rebuild
- [x] Install shadcn/ui and wire its CSS variables to the same tokens — `background`, `foreground`, `primary`, `muted`, `accent`, `border`, `ring` all resolve to design tokens
- [x] Red reserved for deterministic conflict; green only for completed and validated actions — enforced by `--color-*: initial`, which deletes Tailwind's default palette so `bg-red-500` no longer exists
- [x] Tabular numerals for amounts and timestamps — `[data-numeric]` in the base layer
- [x] Verify contrast reaches AA on every status indicator — measured; `--t-3` corrected to 4.54:1 in the source
- [x] Use `PerfectScrollArea` for bounded scroll regions per the architecture rules — shell main column and sidebar; thumb/rail themed from tokens in `components.css`

## Done when

The dev-mode app matches the design direction on colour, spacing, and type scale; every
status indicator passes AA contrast; and no status is conveyed by colour alone.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/web.md`

## Notes

**Two deviations from the plan above, both deliberate.**

1. **No `tailwind.config.ts`.** Tailwind v4 is CSS-first; the file the plan named no longer
   exists in that version. The theme is a `@theme` block in `src/styles/app.css` instead, and
   it uses `@theme inline` so the emitted utilities carry `var(--token)` rather than a resolved
   value — which is what lets the `[data-theme]` switch repaint without a rebuild.
2. **Tailwind's default colour palette is deleted** (`--color-*: initial`). `design/DESIGN.md`
   reserves red for deterministic conflict and green for completed, validated actions. While
   `bg-red-500` still existed, that rule could only be enforced by review; now the class
   produces nothing and the misuse surfaces where it is typed.

Fonts are self-hosted via `@fontsource` rather than the mockup's Google Fonts `<link>`:
`brief/03_ANTREAN_REVIEW.md` § 9.3 requires the app to work with no external network, and the
demo runbook is offline. Only the latin subsets are imported — shipping all of them cost
675 kB for scripts this app never renders.

The 9 px micro-label question is resolved: raised to 11 px by the project owner on 31 Aug,
recorded in `design/DESIGN.md` § Deviasi and applied in `design/tokens.css` at source.
