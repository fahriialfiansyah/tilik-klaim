# Task 00 — Port design tokens and wire Tailwind

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ⏸ Blocked — waiting on the design team
**Foundation:** no
**Autonomous:** no — one-time styling setup.

> **Blocked, by design.** `design/tokens.css` does not exist yet; per
> [`design/DESIGN.md`](../../../../design/DESIGN.md) the visual detail is owned by the design
> team. This task cannot close until that file lands. The direction is already fixed, so
> nothing else in this sprint waits on it — the other tasks build structure and behaviour.

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

- [ ] **Blocked:** obtain `design/tokens.css` from the design team
- [ ] Install and configure Tailwind
- [ ] Port tokens into `src/styles/tokens.css`
- [ ] Bind the Tailwind theme to the tokens
- [ ] Install shadcn/ui and wire its CSS variables to the same tokens
- [ ] Red reserved for deterministic conflict; green only for completed and validated actions
- [ ] Tabular numerals for amounts and timestamps
- [ ] Verify contrast reaches AA on every status indicator
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
