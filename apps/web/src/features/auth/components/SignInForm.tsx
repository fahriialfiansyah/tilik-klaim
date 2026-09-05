import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { startSession } from '@/features/auth/api'
import { DEMO_ACCOUNTS, credentialLine, type DemoAccount } from '@/features/auth/accounts'
import { RoleMatrix } from '@/features/auth/components/RoleMatrix'
import { ROLE_LABEL } from '@/features/auth/labels'
import { useSession } from '@/features/auth/useSession'
import { ApiError, NetworkError } from '@/lib/http'

/**
 * Choose a row in the matrix, then sign in as that person.
 *
 * Four states, as `design/DESIGN.md` requires of anything that fetches: **memuat** while the
 * request is in flight, **kosong** while either field is blank (submit disabled, and the reason
 * said out loud rather than left to a greyed button), **galat** for a refusal or an unreachable
 * service, and **nonaktif** for the one refusal that is not the operator's mistake — a
 * deactivated account, which is told apart on purpose because the credentials were right.
 *
 * Choosing a row fills both fields; both stay editable, because the fields are the real control
 * and the matrix is a shortcut. Somebody typing a fourth address gets the same refusal an
 * unknown account would get anywhere else.
 */
type Status =
  | { readonly kind: 'idle' }
  | { readonly kind: 'submitting' }
  | { readonly kind: 'refused'; readonly message: string; readonly deactivated: boolean }

const COPY_FEEDBACK_MS = 1600

const FIELD_CLASSES =
  'h-10 w-full rounded-md border border-line bg-card px-3 font-mono text-small text-ink outline-none placeholder:text-ink-3 focus-visible:border-brand focus-visible:ring-2 focus-visible:ring-ring/40'

export function SignInForm() {
  const signIn = useSession((state) => state.signIn)
  const [chosen, setChosen] = useState<DemoAccount>(DEMO_ACCOUNTS[0])
  const [email, setEmail] = useState(DEMO_ACCOUNTS[0].email)
  const [passcode, setPasscode] = useState(DEMO_ACCOUNTS[0].passcode)
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [copied, setCopied] = useState(false)

  const incomplete = email.trim() === '' || passcode.trim() === ''
  const busy = status.kind === 'submitting'

  // The row and the fields are one choice; changing the row rewrites both and clears whatever
  // the previous attempt was refused for, because that refusal was about a different account.
  useEffect(() => {
    setEmail(chosen.email)
    setPasscode(chosen.passcode)
    setStatus({ kind: 'idle' })
  }, [chosen])

  async function onCopy() {
    // Never report a copy that did not happen — the same rule `AppHeader.onCopy` follows. The
    // credentials stay on screen and selectable either way, so a failed copy costs nothing, but
    // a false "tersalin" would cost the demo a confused pause.
    if (await writeClipboard(credentialLine(chosen))) {
      setCopied(true)
      window.setTimeout(() => setCopied(false), COPY_FEEDBACK_MS)
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (incomplete || busy) {
      return
    }
    setStatus({ kind: 'submitting' })
    try {
      // Writing the session is the whole of it — `LoginPage` watches the store and navigates,
      // so there is one place that decides where each role lands.
      signIn((await startSession(email.trim(), passcode)).user)
    } catch (failure) {
      setStatus(describeFailure(failure))
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3" noValidate>
      <fieldset className="m-0 min-w-0 border-0 p-0">
        <legend className="sr-only">Pilih akun contoh</legend>
        <RoleMatrix chosen={chosen} onChoose={setChosen} />
      </fieldset>

      <div className="grid grid-cols-1 items-end gap-4 rounded-md border border-brand-line bg-brand-soft px-4 py-[14px] md:grid-cols-[1fr_1fr_auto]">
        <div className="flex flex-col gap-[6px]">
          <label htmlFor="signin-email" className="text-small font-medium text-ink">
            Email petugas
          </label>
          <input
            id="signin-email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="nama@rsud-demo.example"
            className={FIELD_CLASSES}
            data-numeric
          />
        </div>

        <div className="flex flex-col gap-[6px]">
          <label htmlFor="signin-passcode" className="text-small font-medium text-ink">
            Kode demo
          </label>
          <input
            id="signin-passcode"
            /*
              `type="text"`, not `type="password"`. The value is printed on this very page; a
              masked field would imply a secret and would make the demo harder to read from the
              back of a room. Naming things accurately is the whole argument of this screen.
            */
            type="text"
            autoComplete="off"
            spellCheck={false}
            value={passcode}
            onChange={(event) => setPasscode(event.target.value)}
            placeholder="demo-…-2026"
            className={FIELD_CLASSES}
            data-numeric
          />
        </div>

        <Button type="submit" size="lg" disabled={incomplete || busy}>
          {busy ? 'Memeriksa…' : `Masuk sebagai ${ROLE_LABEL[chosen.role]}`}
        </Button>
      </div>

      {status.kind === 'refused' ? (
        <p
          role="alert"
          className={
            status.deactivated
              ? 'rounded-md border border-notice-line bg-notice-bg px-3 py-[10px] text-small text-notice'
              : 'rounded-md border border-band-conflict-line bg-band-conflict-bg px-3 py-[10px] text-small text-band-conflict'
          }
        >
          <span className="font-semibold">
            {status.deactivated ? 'Akun nonaktif: ' : 'Tidak dapat masuk: '}
          </span>
          {status.message}
        </p>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <p aria-live="polite" className="text-meta text-ink-3">
          {incomplete
            ? 'Isi email dan kode demo terlebih dahulu.'
            : 'Kedua bidang tetap dapat disunting. Baris di atas hanya jalan pintas.'}
        </p>
        <Button type="button" variant="outline" size="sm" onClick={onCopy}>
          {copied ? 'Tersalin' : 'Salin kredensial'}
        </Button>
      </div>
    </form>
  )
}

/** `false` when the browser refused the write — no clipboard API, or permission denied. */
async function writeClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

/** Turns a thrown failure into the sentence the operator reads, and which state drew it. */
function describeFailure(failure: unknown): Status {
  if (failure instanceof ApiError) {
    return {
      kind: 'refused',
      message: failure.message,
      deactivated: failure.code === 'SESSION_ACCOUNT_DEACTIVATED',
    }
  }
  if (failure instanceof NetworkError) {
    return {
      kind: 'refused',
      message: 'Layanan tidak merespons. Ini bukan berarti kode demo salah. Coba lagi.',
      deactivated: false,
    }
  }
  return {
    kind: 'refused',
    message: 'Terjadi kegagalan yang tidak dikenali. Coba lagi.',
    deactivated: false,
  }
}
