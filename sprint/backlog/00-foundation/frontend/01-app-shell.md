# Task 01 — App shell, config-driven menu, and four route stubs

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** no — one-time project setup.

## Goal

A React application that builds and typechecks, serving the four routes from
`sprint/00-app-spec.md` inside a non-overlapping shell, with navigation driven by config.

## Files to touch

- `apps/web/package.json` — React 18, React Router, Zustand, Rsbuild, TypeScript
- `apps/web/rsbuild.config.ts` — build configuration and dev server
- `apps/web/tsconfig.json` — strict mode plus the `@/*` path alias
- `apps/web/src/config/menu/app-menu.ts` — `APP_MENU` as the navigation source of truth
- `apps/web/src/components/layouts/AppShell.tsx` — header, sidebar, main; reserved space each
- `apps/web/src/App.tsx` — route table
- `apps/web/src/index.tsx` — entrypoint
- `apps/web/src/pages/*/` — one stub per page

## Skills to consult

- `.claude/rules/architecture.md` § Web UI Enforcement — shell layout and menu-config rules
- `sprint/00-app-spec.md` — page inventory and routes

## TODOs

- [x] React 18 + TypeScript + Rsbuild per the stack rules
- [x] `APP_MENU` in `src/config/menu/`; the shell renders from it and hardcodes no route list
- [x] Shell layout: root `flex h-screen flex-col overflow-hidden`, header `h-12`, body `flex min-h-0 flex-1`, sidebar `w-[220px]`, main `flex-1 overflow-auto`
- [x] Four routes wired: `/`, `/cases/:id`, `/ingest`, `/evaluation`
- [x] Synthetic-data badge in the header, not dismissible
- [x] Strict TypeScript; `noUnusedLocals` and `noUnusedParameters` on
- [x] `npx tsc --noEmit` passes
- [x] `npx rsbuild build` succeeds

## Done when

`npm run typecheck` reports no errors and `npx rsbuild build` produces a bundle; all four
routes render inside the shell without regions overlapping.

**Verified 2026-08-30:** typecheck clean; build 165.6 kB total (55.0 kB gzip).

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified (typecheck clean, build succeeded)
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/web.md`

## Notes

Tailwind is **not** installed yet. The shell uses Tailwind-shaped class names so the layout
contract is already expressed, but they are inert until `design/tokens.css` arrives from the
design team. Wiring Tailwind is part of `04-review-slice/frontend/00-port-design-tokens.md`,
which is blocked on that file.

shadcn/ui is likewise deferred — pulling in primitives before there are tokens to bind them
to would mean styling twice.
