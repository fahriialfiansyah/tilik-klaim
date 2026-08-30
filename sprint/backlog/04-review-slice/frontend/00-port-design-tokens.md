# Task 00 — Port design tokens and wire Tailwind

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned — design blocker cleared, awaiting go-ahead on the toolchain
**Foundation:** no
**Autonomous:** no — one-time styling setup.

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
- [ ] Install and configure Tailwind
- [ ] Port tokens into `src/styles/tokens.css` — copy from `design/tokens.css`, do not retype
- [ ] Bind the Tailwind theme to the tokens
- [ ] Install shadcn/ui and wire its CSS variables to the same tokens
- [ ] Red reserved for deterministic conflict; green only for completed and validated actions
- [ ] Tabular numerals for amounts and timestamps
- [x] Verify contrast reaches AA on every status indicator — measured; only `--t-3` falls short (4.41:1), tracked in `design/DESIGN.md`
- [ ] Use `PerfectScrollArea` for bounded scroll regions per the architecture rules

## Done when

The dev-mode app matches the design direction on colour, spacing, and type scale; every
status indicator passes AA contrast; and no status is conveyed by colour alone.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/web.md`

## Notes

Until this unblocks, the other frontend tasks use plain semantic markup with Tailwind-shaped
class names. Structure and behaviour are testable without final styling; restyling later is
cheap, whereas rebuilding behaviour is not.
