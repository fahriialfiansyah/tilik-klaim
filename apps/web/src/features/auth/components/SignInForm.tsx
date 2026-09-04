import { useEffect, useRef, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { AccountCards } from '@/features/auth/components/AccountCards'
import { startSession } from '@/features/auth/api'
import type { DemoAccount } from '@/features/auth/accounts'
import { useSession } from '@/features/auth/useSession'
import { ApiError, NetworkError } from '@/lib/http'

/**
 * The right half of `/login`.
 *
 * Four states, as `design/DESIGN.md` requires of anything that fetches: **memuat** while the
 * request is in flight, **kosong** while either field is blank (submit disabled, and the reason
 * said out loud rather than left to a greyed button), **galat** for a refusal or an unreachable
 * service, and **nonaktif** for the one refusal that is not the operator's mistake — a
 * deactivated account, which is told apart on purpose because the credentials were right.
 */
type Status =
  | { readonly kind: 'idle' }
  | { readonly kind: 'submitting' }
  | { readonly kind: 'refused'; readonly message: string; readonly deactivated: boolean }

const FIELD_CLASSES =
  'h-10 w-full rounded-md border border-line bg-card px-3 text-body text-ink outline-none placeholder:text-ink-3 focus-visible:border-brand focus-visible:ring-2 focus-visible:ring-ring/40'

export function SignInForm() {
  const signIn = useSession((state) => state.signIn)
  const [email, setEmail] = useState('')
  const [passcode, setPasscode] = useState('')
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [focusSubmit, setFocusSubmit] = useState(false)
  const submitRef = useRef<HTMLButtonElement>(null)

  // Focus has to wait for the commit that fills the fields: until then the submit button is
  // still `disabled`, and focusing a disabled button silently does nothing. Calling `focus()`
  // straight from the click handler looked right and moved focus nowhere.
  useEffect(() => {
    if (focusSubmit) {
      submitRef.current?.focus()
      setFocusSubmit(false)
    }
  }, [focusSubmit])

  const incomplete = email.trim() === '' || passcode.trim() === ''
  const busy = status.kind === 'submitting'

  function usePersona(account: DemoAccount) {
    setEmail(account.email)
    setPasscode(account.passcode)
    setStatus({ kind: 'idle' })
    // Focus lands on submit, not back in a field: the credentials are already correct, so the
    // only thing left to do is press Enter. Switching persona mid-demo is one click and a key.
    setFocusSubmit(true)
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
    <div className="flex flex-col gap-7">
      <div>
        <h2 className="text-title font-semibold text-ink text-pretty">Masuk</h2>
        <p className="mt-2 max-w-[52ch] text-body leading-[1.55] text-ink-2 text-pretty">
          Halaman ini <strong className="font-semibold text-ink">memilih peran</strong> untuk
          prototipe. Ia tidak mengamankan apa pun: kode demo tertera di bawah dan disimpan apa
          adanya. Penegakan akses tingkat perusahaan tercatat sebagai kebutuhan produksi, bukan
          fitur yang sudah dibangun.
        </p>
      </div>

      <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
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
              {status.deactivated ? 'Akun nonaktif — ' : 'Tidak dapat masuk — '}
            </span>
            {status.message}
          </p>
        ) : null}

        <div className="flex items-center gap-3">
          <Button ref={submitRef} type="submit" size="lg" disabled={incomplete || busy}>
            {busy ? 'Memeriksa…' : 'Masuk'}
          </Button>
          <p aria-live="polite" className="text-meta text-ink-3">
            {incomplete ? 'Isi email dan kode demo terlebih dahulu.' : null}
          </p>
        </div>
      </form>

      <AccountCards onUse={usePersona} />
    </div>
  )
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
      message: 'Layanan tidak merespons. Ini bukan berarti kode demo salah — coba lagi.',
      deactivated: false,
    }
  }
  return {
    kind: 'refused',
    message: 'Terjadi kegagalan yang tidak dikenali. Coba lagi.',
    deactivated: false,
  }
}
