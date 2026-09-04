# Task 01 — Login page, profile menu, role-aware navigation, user management

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../backend/01-roles-session-and-user-store.md`](../backend/01-roles-session-and-user-store.md)

## Files to touch

- `src/features/auth/{types,labels,accounts,api,useSession,permissions,matrix}.ts`
- `src/features/auth/access-matrix.json` — **generated**; see `scripts/export_access_matrix.py`
- `src/features/auth/components/{SignInForm,RoleMatrix,ClaimTexture,ProfileMenu,RequireSession}.tsx`
- `src/features/admin/users/{types,api,labels,format,useUsers}.ts`
- `src/features/admin/users/components/{UserTable,UserAuditPanel,UsersPlaceholders}.tsx`
- `src/pages/login/LoginPage.tsx`, `src/pages/admin-users/AdminUsersPage.tsx`
- `src/config/menu/app-menu.ts`, `src/App.tsx`, `src/lib/http.ts`
- `src/components/layouts/{AppHeader,AppSidebar}.tsx`
- `src/components/ui/{button,dropdown-menu}.tsx`, `src/components/brand/TilikKlaimMark.tsx`
- `src/assets/favicon.svg`, `rsbuild.config.ts`

## TODOs

- [x] `/login` outside `AppShell`, locked to one viewport (`h-svh`), asserted by a Playwright spec
- [x] **The page is the ADR-0006 § 2 access matrix** — rows are people, columns are capabilities
- [x] Matrix generated from `app/service/access.py`; a backend drift test fails on a stale copy
- [x] Selection is a real radio group inside a real `<table>`; arrow keys walk the personas
- [x] Every cell says *Boleh* / *Tidak* in words; tick and cross are `aria-hidden`
- [x] Background generated from the product's own claim-line shape — no third-party imagery
- [x] Competition context line, including *bukan produk resmi BPJS Kesehatan*
- [x] The mark draws itself once on load, ~700 ms, honouring `prefers-reduced-motion`
- [x] `Salin kredensial` reports success only when the clipboard write resolved
- [x] Four states: memuat, kosong, galat, nonaktif; a deactivated account is named apart
- [x] `AKUN SIMULASI` and `DATA SINTETIK`, neither dismissible, no code path hides either
- [x] Profile menu on Radix `DropdownMenu`; `analis casemix` deleted
- [x] Logout warns before discarding an unsaved disposition draft
- [x] Menu declares roles; sidebar and `RequireSession` both render from it
- [x] `/admin/users`: real `<table>`, `<th scope>`, `PerfectScrollArea`, four states
- [x] Self-row controls disabled and the reason said out loud, not left to a greyed box
- [x] `X-Actor-Role` and `X-Actor-Id` from the session; `ACTOR_ROLE` constant deleted
- [x] Favicon redrawn for 16 px, and guarded: the first one was unparseable XML and every
      browser silently showed its own globe (`favicon.test.ts`)
- [x] 55 new vitest specs (239 total), 16 new Playwright specs (40 total), tsc clean

## Rejected first attempt

The first build was a brand panel left, form right — the layout every dashboard ships — and it
**scrolled**: three stacked account cards made the page ~1.240 px tall at 1440×900. The owner
rejected it, correctly. Three genuinely different concepts were then drawn (the mark as layout, a
hospital staff badge, and the access matrix); the owner chose the matrix.

## Acceptance

`/login` does not scroll at 1440×900; the matrix reproduces the ADR-0006 § 2 rows and cannot show
a column the server does not define; the sidebar renders only reachable routes for all three
roles; a forbidden route redirects rather than rendering; the profile menu closes on Escape and
returns focus to its trigger; no icon on the login page or in the profile menu is a robot or a
sparkle.

## Notes

Hiding a link is a courtesy. The refusal is the server's, and `tests/test_access.py` owns it.
