import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { DEMO_ACCOUNTS, credentialLine, type DemoAccount } from '@/features/auth/accounts'
import { ROLE_DESCRIPTION, ROLE_LABEL } from '@/features/auth/labels'
import { cn } from '@/lib/utils'

const COPY_FEEDBACK_MS = 1600

/**
 * The three demo accounts, with the credentials printed on them.
 *
 * Printing them is the point: this is persona selection wearing a credential-shaped interface
 * (ADR-0006 § 3), and hiding the passcodes would suggest they protect something.
 *
 * `Salin` copies `email · passcode`; `Pakai` fills the form and moves focus to the submit
 * button, so switching persona mid-demo is one click and one Enter.
 */
const ROLE_ACCENT: Readonly<Record<DemoAccount['role'], string>> = {
  reviewer: 'bg-band-context-bg border-band-context-line text-band-context',
  senior_reviewer: 'bg-band-signal-bg border-band-signal-line text-band-signal',
  admin: 'bg-brand-soft border-brand-line text-brand',
}

export function AccountCards({
  onUse,
}: {
  readonly onUse: (account: DemoAccount) => void
}) {
  const [copied, setCopied] = useState<string | null>(null)

  async function onCopy(account: DemoAccount) {
    // Never report a copy that did not happen — the same rule `AppHeader.onCopy` follows. The
    // credentials stay on screen and selectable either way, so a failed copy costs nothing but
    // a false "tersalin" would cost the demo a confused pause.
    if (await writeClipboard(credentialLine(account))) {
      setCopied(account.staffToken)
      window.setTimeout(() => setCopied(null), COPY_FEEDBACK_MS)
    }
  }

  return (
    <section aria-labelledby="accounts-heading" className="flex flex-col gap-3">
      <h2 id="accounts-heading" className="font-mono text-micro font-semibold tracking-label text-ink-3">
        AKUN CONTOH
      </h2>
      <ul className="flex flex-col gap-[10px]">
        {DEMO_ACCOUNTS.map((account) => (
          <li
            key={account.staffToken}
            className="rounded-md border border-line bg-card px-[14px] py-3"
          >
            <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
              <div className="min-w-0">
                <p className="flex items-center gap-2 text-body font-semibold text-ink">
                  {account.fullName}
                  <span data-numeric className="font-mono text-meta font-medium text-ink-3">
                    {account.staffToken}
                  </span>
                </p>
                <p className="mt-[3px] text-meta text-ink-2">{ROLE_DESCRIPTION[account.role]}</p>
              </div>
              <span
                className={cn(
                  'shrink-0 rounded-md border px-[10px] py-[3px] text-small font-semibold',
                  ROLE_ACCENT[account.role],
                )}
              >
                {ROLE_LABEL[account.role]}
              </span>
            </div>

            <p
              data-numeric
              className="mt-[10px] break-all rounded-sm bg-sunk px-[10px] py-[6px] font-mono text-meta text-ink-2"
            >
              {credentialLine(account)}
            </p>

            <div className="mt-[10px] flex items-center gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => onCopy(account)}>
                {copied === account.staffToken ? 'Tersalin' : 'Salin'}
              </Button>
              <Button type="button" variant="subtle" size="sm" onClick={() => onUse(account)}>
                Pakai
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </section>
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
