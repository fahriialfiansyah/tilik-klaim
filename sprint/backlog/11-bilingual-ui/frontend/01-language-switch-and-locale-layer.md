# Task 01 — Language switch, locale resources, and the label layer that follows it

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../backend/01-locale-aware-catalogs.md`](../backend/01-locale-aware-catalogs.md)

## Files to touch

- `src/modules/i18n/{config,locales,useLocale,translateOr,index,i18next.d}.ts`
- `src/modules/i18n/LanguageSwitcher.tsx` — **new**
- `src/locales/{id,en}/*.json` + `index.ts` — **new**: ten namespaces per language
- `src/features/*/labels.ts` — seven modules, constants → hooks
- `src/config/menu/app-menu.ts` — `label` removed; `id` **is** the translation key
- `src/components/layouts/{AppHeader,AppSidebar}.tsx`, `src/components/ui/dialog.tsx`
- `src/features/{auth,admin,review}/**` — every component carrying user-facing text
- `src/pages/{queue,case-detail,ingest,evaluation,admin-users,login}/*.tsx`
- `src/lib/http.ts`, `src/index.tsx`, `src/test/setup.ts`

## TODOs

- [x] `i18next` + `react-i18next`; resources **bundled**, not fetched — a screen that loads its
      words over the network is a screen that can render with none of them
- [x] Ten namespaces mirroring the feature tree, `common` first as the default
- [x] `CustomTypeOptions` typed from the Indonesian tree, so a key typo is a compile error
- [x] Switch in the header beside the theme toggle, and on `/login` before the badges
- [x] The trigger shows the **current** language, not the one it would switch to
- [x] Each entry named in its own language, so a reader who cannot read the screen can leave it
- [x] `menuitemradio` + `aria-checked`; the tick is decoration
- [x] Choice persisted, and `<html lang>` kept truthful for screen-reader pronunciation
- [x] **Every `*_LABELS` constant became a hook.** A module-level record is read once at load,
      so the header would have switched language and left every table and badge behind
- [x] `translateOr` for the three runtime-keyed lookups (capabilities, audit kinds, stored
      fields) — one cast in one place, `exists()` rather than comparing to the key
- [x] Non-component callers (`csv.ts`, `useUsers.ts`, `limits.ts`, `format.ts`, `http.ts`,
      `store.ts`) read the running instance: a CSV exported from an English screen is English
- [x] `Accept-Language` on every API call, including the briefing SSE stream
- [x] `key-parity.test.ts`: identical keys both ways, matching placeholders, no blank values
- [x] `language-switch.test.tsx`: a live switch re-renders components already on screen
- [x] Governance guards moved to the locale files and **strengthened** — the security disclaimer
      is now asserted in both languages, where before it was asserted in one
- [x] 42 files / 333 specs green; tsc clean

## Acceptance

Switching the language re-renders everything already on screen, not only the header. The key
parity test fails if a key or a placeholder exists in one language and not the other. `/login`
disclaims security in both languages. No screen mixes the two.

## Notes

The parity test earned its place before it was even committed: a batch edit replaced the whole
of `admin.undo` instead of merging into it, taking four keys with it. Nothing else in the suite
noticed, and the screens using them would have rendered raw key strings.
