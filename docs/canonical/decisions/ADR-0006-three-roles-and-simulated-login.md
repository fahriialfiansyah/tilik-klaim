> Status: canonical — read-only. Perubahan hanya lewat ADR baru.

# ADR-0006 — Three roles, a simulated login, and a user-management page

- **Status:** Accepted — owner decision 2026-09-04; implemented as Sprint 10 the same day
- **Date:** 2026-09-04
- **Scope:** Role identifiers across the whole system; two new pages (`/login`, `/admin/users`);
  a `users` table with one Alembic migration; three additive endpoints. **No change to the seven
  frozen endpoints or to the eighth briefing endpoint.**
- **Owner section:** [`sprint/00-app-spec.md`](../../../sprint/00-app-spec.md) § 1 (page inventory)
  and § 2 (global elements)
- **Supersedes:** two statements, both named below and both quoted rather than paraphrased —
  `sprint/00-app-spec.md` § 1 *"Empat halaman. Tidak lebih"* / *"Tidak ada halaman login. Peran
  disimulasikan"*, and the role names in
  [`03_architecture.md`](../03_architecture.md) § Security and observability by design.

**Cross-reference (jangan salin isinya ke sini):**

- Scope tiers, and the OUT OF SCOPE row this ADR is built around → [01_product_decision.md](../01_product_decision.md) § 13
- Role model, `X-Actor-Role`, and the production-enforcement sentence → [03_architecture.md](../03_architecture.md) § Security and observability by design
- Separation of duties, the role/access matrix deliverable, append-only audit → [07_privacy_threat_model.md](../07_privacy_threat_model.md) § Product controls, § Governance deliverables
- Append-only audit events, and why a correction appends → [ADR-0001](ADR-0001-canonical-model.md)
- Locked visual direction, four mandatory states, the badge that cannot be dismissed → [`design/DESIGN.md`](../../../design/DESIGN.md)
- Pages, widgets, binding display rules → [`sprint/00-app-spec.md`](../../../sprint/00-app-spec.md)

---

## Context

Three facts are true of the system as it stands on 4 September, and together they make the
current arrangement worse than either building roles properly or not having them at all.

**1. Four names exist for three roles, and none of them agree.**

| Where | Names it uses |
|---|---|
| `03_architecture.md` § Security | `analyst`, `senior reviewer`, `administrator` |
| `app/service/disposition.py` | `reviewer`, `senior_reviewer`, `auditor` |
| `apps/web/src/components/layouts/AppHeader.tsx` | `analis casemix` — a hardcoded constant matching nothing |
| `apps/web/src/features/review/case-detail/api.ts` | `ACTOR_ROLE = 'reviewer'`, hardcoded, sent on every call |

A reviewer of this code cannot tell which list is authoritative, and the one a judge actually
*sees* — `analis casemix` in the header — is the one that exists nowhere else. The role model
is currently a decoration.

**2. `auditor` and `senior_reviewer` are the same role wearing two names.** They appear in
exactly two frozensets, `AUDIT_READER_ROLES` and `REOPEN_ROLES`, and `auditor` is a member of
both wherever `senior_reviewer` is. There is no capability one has and the other lacks, no seed
that creates an `auditor`, and no UI that selects one. It is a name with no behaviour behind it.

**3. Separation of duties is a stated control with nothing enforcing it.**
`07_privacy_threat_model.md` § Product controls names "separation of duties" under
Identification and lists a "Role/access matrix" among the Governance deliverables. Today every
request carries `X-Actor-Role: reviewer` from one hardcoded constant, so the matrix is a
document describing a system that does not branch on it.

The competing pressure is real and is why this ADR is needed rather than assumed:
`01_product_decision.md` § 13 puts **"Enterprise IAM"** in OUT OF SCOPE and **"Basic role
simulation"** in SHOULD HAVE, and `sprint/00-app-spec.md` § 1 puts "many dashboards or dummy
menus" out of scope by way of the same table. A login page is exactly the kind of feature that
can be built to *look* like it satisfies a security requirement while satisfying nothing — and
this project's whole credibility argument is that it does not overclaim.

## Decision

### 1. Three role identifiers, chosen and final

| Identifier | Label (UI, Indonesian) | What it is for |
|---|---|---|
| `reviewer` | Peninjau | Screens and dispositions claims |
| `senior_reviewer` | Peninjau Senior | The same, plus reopening a case someone else dismissed |
| `admin` | Administrator | Manages **users**. Never touches a claim |

`auditor` is **retired**, not renamed-and-kept: its capability set was identical to
`senior_reviewer`'s, so keeping both would preserve the ambiguity this ADR exists to remove.
Every `auditor` in code and tests becomes `senior_reviewer`; the assertions those tests make
(*a permitted role may reopen; `reviewer` may not*) are unchanged — only the name of the
permitted role moves.

The canonical `analyst` / `senior reviewer` / `administrator` triple is replaced by
`reviewer` / `senior_reviewer` / `admin`, because:

- `analyst` reads as someone who *analyses data*; this person judges a specific claim and signs
  their name to it. `reviewer` is what `01_product_decision.md` § 07 calls them
  ("Hospital casemix / anti-fraud officer conducting pre-submission review") and what the code
  has always called them.
- `administrator` becomes `admin` with a **deliberately narrower meaning**. It administers
  *users* — role and active flag, nothing else. It is not a superuser, has no elevated view of
  any case, and cannot read a case audit trail. Shortening the name is the smaller half of this
  change; narrowing what it means is the point.

Identifiers stay English, labels stay Indonesian, exactly as elsewhere.

### 2. The access matrix, enforced on the server

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

**Hiding a button is not access control.** Every ❌ in this table is refused by the API with a
stable error code and asserted by a test, and the sidebar's filtering is a courtesy on top of
that — not the mechanism. The existing `AUDIT_READER_ROLES` / `REOPEN_ROLES` frozensets in
`app/service/disposition.py` are extended into one place that answers "may this role do this",
rather than a second parallel mechanism being introduced beside them.

**`admin` sees exactly one page.** That is thin, and it is meant to be: an administrator who
could also open a case would be the counterexample to the control this table exists to
demonstrate. If it proves too thin to be worth showing, the answer is to say so — not to widen
it quietly.

### 3. The login is persona selection with a credential-shaped interface

`/login` presents an email field, a passcode field, and three visible account cards carrying
the credentials in plain text. Credentials are checked against seeded rows in the `users` table.

**This is not authentication, and the page says so.** There is no password hashing, no JWT, no
session store, no token expiry, no IAM. A permanent, non-dismissible **`AKUN SIMULASI`** badge
sits beside the existing **`DATA SINTETIK`** badge, and the page's own copy states that the
sign-in selects a persona for the prototype.

Why credential-shaped at all, rather than three buttons:

- The *interface* being credential-shaped is what makes the RBAC demonstrable in ninety seconds:
  a judge sees a real sign-in, a real refusal for a deactivated account, and a visibly different
  application behind each of the three accounts.
- The *implementation* being honest is what keeps it inside the OUT OF SCOPE row. Hashing a
  passcode that is printed on the same screen would be theatre — it would protect nothing and
  would mislead anyone reading this code into thinking a security boundary exists.

The stored column is therefore named **`demo_passcode`**, never `password` or `password_hash`,
and both the column comment and the model docstring state that it is plain text on purpose.
A name is the cheapest documentation there is, and `password_hash` on a value shown on screen
would be a lie told in a schema.

### 4. `X-Actor-Role` stays forgeable, and that is written down

The frontend sends `X-Actor-Role` and a new `X-Actor-Id` from the stored session on every
request. **Anyone with `curl` can send any value for either.** This is unchanged from today and
is not fixed by this ADR:

- what the server now does is *branch* on the role, refuse what the matrix refuses, and record
  the claimed actor on every audit event;
- what the server still does not do is *verify* that the caller is who the header says.

`03_architecture.md` already requires that "prototype may simulate roles but must document
production enforcement". This ADR is that documentation, and the sentence is repeated in
`app/router/users.py`'s module docstring so it is read by whoever changes the code, not only by
whoever reads the docs. Production enforcement — a Bearer identity issued by an authenticated
session, checked before the role is trusted — is a **stated future requirement, not a shipped
feature**, and no screen, README, or proposal slide may describe it otherwise.

**The default when no role header arrives stays `reviewer`.** Existing tests send no
`X-Actor-Id` and many send no role at all, and the seven frozen endpoints' documented behaviour
depends on that default. Changing it would break a contract to gain nothing: the header is
forgeable either way, so the default is a compatibility choice, not a security one. Every
request the web app makes carries both headers explicitly.

### 5. Four pages become six

`sprint/00-app-spec.md` § 1 currently reads *"Empat halaman. Tidak lebih"*. It becomes six.
The OUT OF SCOPE row that sentence defends is **"many dashboards or dummy menus"**, and the test
for a dummy menu is whether anything is behind it:

- **`/login`** is not in the sidebar and is not a menu entry at all. It sits outside `AppShell`
  and is the only way into the other five pages. What it selects changes what every one of them
  renders and what the API will accept — a menu with nothing behind it is the opposite of this.
- **`/admin/users`** is the only page one of the three roles can reach, it writes append-only
  audit events under the same guarantee as case disposition (ADR-0001), and it is the concrete
  form of the "Role/access matrix" that `07_privacy_threat_model.md` § Governance deliverables
  already lists as owed. It is not a dashboard; it shows no aggregate and no metric.

Neither page adds a fifth or sixth *reviewer* screen. The reviewer's application is still the
four pages it was.

### 6. Users live in Postgres, and fall back to memory like everything else

A `users` table, one Alembic migration on head `d1a7c3e50f42`, and a
`UserRecord` / `UserStore` / `InMemoryUserStore` / `SqlUserStore` set registered in
`app/store/registry.py` beside the other four. The in-memory fallback is not a convenience here
either: `08_demo_runbook.md` requires an offline run, and a login page that needs a database to
show its account cards would take the whole demo down with Postgres.

The three seeded staff use the RFC 2606 reserved `.example` TLD (`…@rsud-demo.example`) so no
address can ever resolve — the same discipline the vLLM tests apply with `gateway.invalid`.

### 7. What is deliberately not done

- **No fourth role.** Not `auditor`, not a read-only observer, not a superuser.
- **No create and no delete of users.** The synthetic roster is fixed at three; management is
  role change and activate/deactivate, each writing an audit event. A create form would need
  passcode entry, which would need a credential policy, which is the OUT OF SCOPE row again.
- **An admin may not change their own role or deactivate themselves.** Refused on the server
  with its own stable code. Locking the only administrator out of the only administrative page
  is a defect, not a decision the UI should faithfully carry out.
- **No change to the seven frozen endpoints or the briefing endpoint.** The three new endpoints
  (`POST /v1/auth/session`, `GET /v1/users`, `PATCH /v1/users/{id}`) are additive.
- **No new session store.** The chosen persona is held in `localStorage` by the client. There is
  nothing to invalidate server-side because nothing was ever issued.

## Consequences

- The role model becomes a thing the system *does* rather than a thing three documents describe
  differently. `analis casemix` is deleted; the header shows the signed-in person and their role.
- The demo gains a beat it did not have: sign in as `admin`, and the queue is not merely hidden —
  the API refuses it. Separation of duties becomes observable in about ten seconds.
- Every user-management change is answerable: actor, target, before, after, timestamp, appended
  and never edited, exactly like a case disposition.
- **The login page is the first thing a judge sees**, and it is now the most likely place for
  this project to be misread as claiming a security capability. That risk is priced in below.
- One existing test changes: `test_disposition.py`'s reopen case swaps `actor_role="auditor"`
  for `actor_role="senior_reviewer"`. What it asserts is untouched.
- `sprint/00-app-spec.md` § 1 gains two rows and § 2 gains the `AKUN SIMULASI` badge and the
  profile menu. The spec, not this ADR, remains the page and widget authority.

## Kill criteria

Pre-committed and measurable. Each reverts a named piece, not the whole change.

| Criterion | Evidence of failure | Action |
|---|---|---|
| The login reads as a security claim | Any one of three non-domain readers, shown `/login` for 30 seconds, describes it as securing, protecting, or authenticating the system | The badge and copy have failed. Revert `/login` to a plain persona picker — three cards, no fields — and keep the RBAC |
| The admin role is too thin to be worth a page | The owner, after the rehearsal, cannot state in one sentence what `/admin/users` proves | Remove `/admin/users` and the `admin` role; `reviewer` and `senior_reviewer` stand. **Do not widen `admin` instead** |
| RBAC costs the demo its ninety seconds | The 90-second flow overruns on the presentation machine because of the sign-in step | Seed the session in `localStorage` for the demo profile; the login stays reachable but is not on the critical path |
| Roles are enforced only in the UI | Any row of the § 2 matrix passes a UI check but succeeds against the API with a forged header | The feature is not shippable in that state. Fix the server, or revert the row's ❌ to ✅ and correct the matrix |
| A reviewer loses unsaved work to a sign-out | Logging out discards a disposition draft without warning | Defect, fix in place. `store.ts` keeps drafts alive precisely so a refused save costs nothing |

A revert here costs one frontend commit range plus one down-migration. The `users` table has no
foreign key into `cases` or `audit_events`, so dropping it takes nothing with it.
