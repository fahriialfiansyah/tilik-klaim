# Prompt — Login, tiga peran, dan manajemen pengguna

Salin **seluruh blok di antara dua garis `---`** sebagai pesan pertama ke sesi baru.

---

You are continuing **TilikKlaim** — a claim-evidence integrity layer that screens synthetic
SATUSEHAT-shaped JKN claim bundles for four facility risk patterns and requires a logged human
disposition. Healthkathon 2026 entry, category *Efisiensi Risiko pada Fasilitas Kesehatan*.

**Today is 4 September 2026. Registration closes 14 September; the proposal closes 19 September,
internal upload target 18 September.**

WORK DIR: `/Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim`
(git branch `development`, HEAD `3fc7356`, in sync with a PUBLIC GitHub remote. **Do NOT push.**
Commit in small Conventional Commits as you finish each piece — the owner reads the log in the
morning. Leave `scripts/dev.sh` alone; that modification is theirs, in progress.)

READ FIRST, in order: `docs/HANDOVER.md` (state, environment, every trap already hit) ·
`sprint/00-app-spec.md` (pages and binding display rules) · `docs/canonical/01_product_decision.md`
(the ethical core and the kill criteria) · `design/DESIGN.md` (locked visual direction) ·
`docs/qa/MANUAL-QA.md` (what the owner checks by eye).

## Your task

Add **authentication-shaped role selection**, **three roles with enforced RBAC**, a **login page**,
a **profile menu in the top bar**, and an **admin-only user management page**.

**The owner has already decided the four questions below. Do not re-open them.**

1. **Login is credential-shaped but simulated.** A real login form (email + passcode) checked
   against seeded synthetic staff in the database. **No password hashing, no JWT, no session
   store, no Enterprise IAM** — `docs/canonical/01_product_decision.md` puts Enterprise IAM in
   OUT OF SCOPE, and building a half-real auth system would be claiming a capability this project
   cannot support. The login page carries a permanent, non-dismissible **`AKUN SIMULASI`** badge
   beside the existing `DATA SINTETIK` badge.
2. **Admin never touches a claim case.** Separation of duties, which
   `docs/canonical/07_privacy_threat_model.md` names directly. Admin manages users; reviewers
   judge claims. Neither does the other's job.
3. **User management = change role + activate/deactivate.** No create, no delete — the synthetic
   roster is fixed at three. Every change writes an audit event with actor and timestamp.
4. **Users live in Postgres**, with an Alembic migration, following the existing store pattern —
   and falling back to in-memory when no database answers, exactly like every other store.

## Step 0 — write ADR-0006 FIRST, before any code

This change contradicts two canonical statements, and `docs/canonical/` is read-only except
through a new ADR. **Do not write code until the ADR exists.**

- `sprint/00-app-spec.md` § 1: *"Empat halaman. Tidak lebih"* and *"Tidak ada halaman login.
  Peran disimulasikan"*. You are adding two pages (`/login`, `/admin/users`).
- `docs/canonical/03_architecture.md` § Security: *"Role model: analyst, senior reviewer,
  administrator"*. The code today uses `reviewer` / `senior_reviewer` / `auditor` — three
  different names — and the header displays a fourth, `analis casemix`, hardcoded in
  `AppHeader.tsx` and matching nothing.

Write `docs/canonical/decisions/ADR-0006-three-roles-and-simulated-login.md` following the shape
of ADR-0004 and ADR-0005 (status, date, scope, owner section, cross-reference block, context,
decision, consequences, kill criteria). It must state:

- the **three canonical names**, chosen and final: `reviewer`, `senior_reviewer`, `admin`;
  `auditor` is retired because its behaviour was identical to `senior_reviewer`, and the
  canonical `administrator` becomes `admin` with a **narrower** meaning — it administers *users*,
  never claims;
- that the login is **persona selection with a credential-shaped interface**, not authentication,
  and why that is the honest choice given the OUT OF SCOPE row;
- that `X-Actor-Role` remains forgeable by design and that this is documented rather than hidden —
  production enforcement is a stated future requirement, not a shipped feature;
- the page count moves from four to six, and why each addition is not a "dummy menu";
- kill criteria: if the login page reads as a security claim to any non-domain reader, the badge
  and copy have failed and the page reverts to a persona picker.

`docs/` is gitignored — the ADR needs `git add -f` or it is invisible to git.

## The three roles, and what each may do

Identifiers in English, labels in Indonesian, exactly as elsewhere in this codebase.

| Kemampuan | `reviewer` | `senior_reviewer` | `admin` |
|---|---|---|---|
| Antrean `/` dan Detail Kasus `/cases/:id` | ✅ | ✅ | ❌ |
| Catat disposisi | ✅ | ✅ | ❌ |
| Buka kembali kasus yang sudah ditolak | ❌ | ✅ | ❌ |
| Baca riwayat audit kasus | ✅ | ✅ | ❌ |
| Ingest / Demo `/ingest` | ✅ | ✅ | ❌ |
| Audit & Evaluasi `/evaluation` | ✅ | ✅ | ❌ |
| Minta Ringkasan bukti | ✅ | ✅ | ❌ |
| Manajemen pengguna `/admin/users` | ❌ | ❌ | ✅ |
| Baca audit manajemen pengguna | ❌ | ❌ | ✅ |

**Admin sees only the user-management page**, and the sidebar renders only what the role may
reach. This is deliberate and is the whole point of having roles: separation of duties made
visible. If it feels thin in practice, say so in your summary — do not quietly widen it.

**Enforce every row on the server, not only in the UI.** Hiding a button is not access control.
`apps/backend/app/service/disposition.py` already has `AUDIT_READER_ROLES` and `REOPEN_ROLES`;
extend that pattern rather than inventing a second one. A request carrying
`X-Actor-Role: admin` to a disposition endpoint must be refused with a stable error code, and a
test must assert it.

## The three synthetic staff

Seeded, and obviously synthetic. Emails use the RFC 2606 reserved `.example` TLD so they can
never resolve — the same discipline the vLLM tests use with `gateway.invalid`.

| Nama | Token | Peran | Email | Passcode demo |
|---|---|---|---|---|
| Sari Wulandari | `PTG-01` | `reviewer` | `sari.wulandari@rsud-demo.example` | `demo-reviewer-2026` |
| Budi Santoso | `PTG-02` | `senior_reviewer` | `budi.santoso@rsud-demo.example` | `demo-senior-2026` |
| Rina Hartati | `PTG-03` | `admin` | `rina.hartati@rsud-demo.example` | `demo-admin-2026` |

**Name the passcode field `demo_passcode`, never `password` or `password_hash`.** It is stored in
plain text on purpose and displayed on the login page — it protects nothing, and hashing a value
you print on screen is theatre that would mislead a reviewer of this code. Say that in the
column comment and in the model docstring.

## Login page `/login`

**"Wow" here means craft, not decoration.** `design/DESIGN.md` locks the direction: *"Rasa percaya
datang dari hierarki, asal-usul data, dan kejelasan status — bukan dari gradien neon atau efek
chatbot."* A neon-gradient glassmorphism login would violate the design system and undercut the
product's whole credibility argument in front of judges.

**Forbidden:** neon gradients, particle or aurora backgrounds, stacked glassmorphism blur, robot
or sparkle icons, marketing copy, any claim of security.

**Where the impact comes from instead:**

- **Split layout.** Left: a brand panel on `bg-head` (the dark navy the app header already uses)
  carrying `TilikKlaimMark` at large size — it is an evidence chain closing into a loop, and it
  is the best asset this product has. One line of positioning underneath, in working language.
  Right: the form, on `bg-card`.
- **The mark may draw itself once on load** — the arc stroking in over ~700 ms, respecting
  `prefers-reduced-motion`. Motion that means something (a chain closing) rather than ornament.
- Typography hierarchy and generous spacing carry the rest. Both themes must be correct; the
  page is the first thing a judge sees.
- **Three account cards** beside or below the form: name, role badge using the existing band
  colours, `[Salin]` and `[Pakai]` buttons. `Salin` copies `email · passcode` to the clipboard
  with the same feedback pattern `AppHeader.onCopy` already uses — **and never reports success
  for a copy that did not happen**. `Pakai` fills both fields and focuses the submit button, so
  switching persona mid-demo is one click.
- The four mandatory states apply: memuat, kosong, galat, nonaktif. A deactivated account that
  tries to sign in is refused with a sentence naming why.
- `AKUN SIMULASI` and `DATA SINTETIK` badges, neither dismissible.
- **Keyboard-complete**, visible focus throughout, AA contrast, every status carrying a text
  label and never colour alone.

## Top bar profile menu

Right end of `AppHeader.tsx`, after the theme toggle. Replaces the hardcoded `analis casemix`
constant, which must be deleted.

- Trigger: avatar or initials plus the person's name and role label.
- Click opens a dropdown — use the Radix primitive so focus, Escape and click-outside are handled
  for you, matching how `dialog.tsx` is bound to the tokens. Note that this app has **no
  `DialogTrigger`**, and `dialog.tsx` documents why focus return is manual; check whether the
  same applies before assuming.
- Contents: name, email, role label, staff token, and a **`Keluar`** button.
- Logout clears the stored session and returns to `/login`. If a disposition draft is unsaved,
  **warn before discarding it** — `store.ts` keeps drafts alive precisely so a refused save does
  not cost the reviewer their work, and logout must not silently undo that guarantee.

## Admin page `/admin/users`

Senior-level means the table is genuinely good, not that it is large.

- Columns: nama, token, email, peran, status, terakhir masuk.
- Change role via a select; activate/deactivate via a toggle. Both write an audit event
  (`USER_ROLE_CHANGED`, `USER_DEACTIVATED`, `USER_REACTIVATED`) with actor, target, before/after
  and timestamp — append-only, like the case audit, per ADR-0001.
- **An admin may not change their own role or deactivate themselves.** Locking yourself out of
  the only administrative page is a defect, not a decision; refuse it on the server with a stable
  error code and explain it on screen.
- A panel showing the user-management audit trail, newest first.
- Four states: memuat, kosong, galat, nonaktif.
- Real `<table>` semantics, `<th scope>`, keyboard-complete, bounded scroll through
  `PerfectScrollArea` per `.claude/rules/architecture.md`.

## Backend shape

- `apps/backend/app/store/tables.py` — add a `users` table. Follow the existing column
  conventions (`String(ID_LENGTH)`, timezone-aware `DateTime`, JSONB where it fits).
- One Alembic migration. Current head is `d1a7c3e50f42`. **Do not fill `sqlalchemy.url` in
  `alembic.ini`** — `migrations/env.py` reads it from `app.config` so the service and its
  migrations cannot diverge.
- `apps/backend/app/store/users.py` — `UserRecord`, `UserStore` Protocol, `InMemoryUserStore`,
  `SqlUserStore`, registered in `app/store/registry.py` beside the others.
- `apps/backend/app/dto/users.py` and `apps/backend/app/router/users.py`. Suggested, additive
  only — **the seven frozen endpoints and the eighth briefing endpoint must not move**:
  `POST /v1/auth/session` (verify credentials, return the user record) ·
  `GET /v1/users` (admin) · `PATCH /v1/users/{id}` (admin; role and active flag).
- Extend `app/errors.py` with stable codes — append, never repurpose an existing one.
- Seed the three staff in `scripts/seed_dev.py` and make `scripts/demo_reset.py` restore them, so
  a demo that toggled an account comes back clean.
- Regenerate `docs/api/openapi.json` with `(cd apps/backend && uv run python scripts/export_openapi.py)`.

## Frontend shape

- `src/features/auth/` — types, api, `useSession` (Zustand, persisted to `localStorage`), labels.
- `src/features/auth/components/` — the login panel, the account cards, the profile menu.
- `src/features/admin/users/` — the management feature. **Domain components never go in bare
  `src/components/`**; `.claude/rules/architecture.md` is explicit.
- `src/config/menu/app-menu.ts` — menu is the single source of truth for navigation. Add the
  routes with the roles that may see them, and render the sidebar from that. Never hardcode a
  route list in a layout component.
- `src/App.tsx` — `/login` sits outside `AppShell`; everything else stays inside it behind a
  guard that redirects to `/login` when there is no session and to the role's landing page when
  the route is not permitted.
- `src/lib/http.ts` — send `X-Actor-Role` and a new `X-Actor-Id` from the session on every
  request. Today `ACTOR_ROLE` is hardcoded to `'reviewer'` in
  `src/features/review/case-detail/api.ts`; that constant goes away.

## Guardrails — non-negotiable

- **The ethical core is in the types and asserted by tests.** The system reports "risiko atau
  anomali yang perlu ditinjau" — never fraud, never a rejection, never a payment action, never a
  sanction. Red is only for deterministic conflict; green only for a completed, validated action,
  and green never marks a claim safe.
- **Tailwind's default palette is deleted** (`--color-*: initial` in `src/styles/app.css`), so
  `bg-red-500` produces nothing on purpose. Use the semantic names: `bg-card`, `bg-head`,
  `text-ink`, `border-line`, `bg-brand`, `text-band-conflict`, `bg-notice-bg`, `text-done`.
- **Never write a real secret into anything git tracks.** The demo passcodes are non-secrets by
  construction and belong in seed code; if you add any genuine credential it goes in
  `apps/backend/.env`, which is gitignored, and `.env.example` documents the name with an empty
  value. A test already asserts this for the vLLM gateway — follow that pattern.
- **`docs/` is gitignored.** New files under it need `git add -f`.
- **`uv sync` in `apps/backend` silently uninstalls `tilik-domain`** and the next test run fails
  with `ModuleNotFoundError`, which reads like broken code. Restore with
  `(cd apps/backend && uv pip install -e ".[dev]" -e ../../packages/domain)`.
- **`BRIEFING_ENABLED=true` is currently set in `apps/backend/.env`.** Leave it; it is the
  owner's. Note that `tests/conftest.py` pins it off so the suite never calls the gateway.
- Immutable models (`frozen=True`), files 200–400 lines, functions under 50, no magic numbers,
  explicit error handling. **TDD: write the failing test first.**

## Tests you must write

**Backend** — RBAC is the point, so test the server, not the button:

- each of the three roles against every protected endpoint, permitted and refused;
- `admin` is refused a disposition, refused a reopen, refused case audit — with the stable code;
- `reviewer` is refused a reopen; `senior_reviewer` is allowed one;
- an admin cannot change their own role or deactivate themselves;
- a deactivated user cannot start a session;
- wrong passcode is refused and **the response never echoes the passcode**;
- every user-management change appends an audit event with actor, target and before/after;
- the seeded roster is exactly three, and `demo_reset.py` restores it.

**Frontend** — pure logic and rendered behaviour:

- the sidebar renders only routes the role may reach (all three roles);
- a route the role may not reach redirects rather than rendering;
- `Pakai` fills both fields; `Salin` reports success only when the clipboard write resolved;
- the profile menu closes on Escape and returns focus to its trigger;
- logout with an unsaved disposition draft warns before discarding;
- no icon in the login page or profile menu is a robot or a sparkle (assert on the imported icon
  set, the way `BriefingView.test.tsx` does with `?raw`).

**Playwright** — sign in as each of the three, confirm what each sees and cannot reach; switch
account mid-session with the account cards; complete the whole flow from the keyboard.

## Verify after every change — all eight, and report the counts

```
(cd apps/backend    && uv run pytest)                 # 467 today
(cd packages/domain && uv run pytest)                 # 23
(cd packages/data   && uv run pytest)                 # 57
(cd packages/model  && uv run pytest)                 # 71
(cd evaluation      && uv run pytest)                 # 47
(cd apps/web        && npx tsc --noEmit)              # silent
(cd apps/web        && npm test)                      # 184
(cd apps/backend    && uv run ruff check app tests)   # All checks passed!
(cd apps/web        && npm run test:e2e)              # 24
```

**Every one of those must still pass.** Existing tests send no `X-Actor-Id` and many send no
role at all — decide deliberately whether the default stays `reviewer` for compatibility, say so
in the ADR, and do not "fix" a green test by weakening what it asserts.

Then: load every screen at <http://localhost:3000> against a seeded database and **look at it**.
Save screenshots of every state, both themes, into `docs/qa/<date>-auth-roles/`, and append a
numbered click-through to `docs/qa/MANUAL-QA.md`. This project's hardest defects were all found
by opening the page, never by the compiler.

Finally: tick the `## TODOs`, set `**Status:** ✅ Done`, append to `changelog/{backend,web}.md`,
add the sprint row to `sprint/01-sprint-planning.md`, and update `sprint/00-app-spec.md` § 1 with
the two new pages and their widgets.

**Not pre-authorised:** pushing to the remote; flipping sprint 06 to `✅` (that is the owner's
signature); real password hashing, JWT, or any session store; changing the seven frozen endpoints
or the briefing endpoint; adding a fourth role.

Confirm you have read the documents listed at the top, write ADR-0006, show it to the owner, and
only then start on the code.

---
