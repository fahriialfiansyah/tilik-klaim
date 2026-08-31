import { useState } from 'react'
import { TilikKlaimMark } from '@/components/brand/TilikKlaimMark'
import { copyStamp, shortStamp, useEngineVersion } from '@/modules/engine-version/useEngineVersion'
import { ThemeToggle } from '@/modules/theme/ThemeToggle'

/** Simulated role. There is no login — `sprint/00-app-spec.md` § 1 records this as A2. */
const ACTIVE_ROLE = 'analis casemix'

const COPY_FEEDBACK_MS = 1600

export function AppHeader() {
  const versions = useEngineVersion((state) => state.versions)
  const [copied, setCopied] = useState(false)
  const stamp = shortStamp(versions)

  async function onCopy() {
    // Never show "tersalin" for a copy that did not happen: the stamp is what an operator
    // quotes when reporting a result. It stays on screen and selectable either way.
    if (await copyStamp(versions)) {
      setCopied(true)
      window.setTimeout(() => setCopied(false), COPY_FEEDBACK_MS)
    }
  }

  return (
    <header className="flex h-[var(--header-h)] shrink-0 items-center justify-between gap-4 bg-head px-4">
      <div className="flex min-w-0 items-center gap-[10px]">
        <TilikKlaimMark className="block size-[30px] shrink-0" />
        <span className="text-lead font-semibold tracking-[.11em] text-ink-inv">TILIKKLAIM</span>
        <span aria-hidden className="h-5 w-px bg-ink-inv/16" />
        <span className="flex items-center gap-[7px] font-mono text-meta text-ink-inv-2">
          PERAN
          {/* G4 — active role marker. */}
          <span className="rounded-full bg-ink-inv/8 px-2 py-[2px] font-medium text-ink-inv">
            {ACTIVE_ROLE}
          </span>
        </span>
      </div>

      <div className="flex items-center gap-[10px]">
        {/* G3 — engine and dataset stamp: copyable, and the way through to /evaluation. */}
        <button
          type="button"
          onClick={onCopy}
          title="Salin penanda versi"
          data-numeric
          className="flex items-center gap-2 rounded-md border border-ink-inv/12 bg-ink-inv/6 px-[10px] py-[6px] font-mono text-meta text-ink-inv transition-colors hover:bg-ink-inv/14"
        >
          {stamp}
          <span className="opacity-60">{copied ? 'tersalin' : 'salin'}</span>
        </button>

        <ThemeToggle />

        {/*
          G1 — synthetic-data badge. `docs/canonical/07_privacy_threat_model.md` requires it on
          every page and forbids dismissing it, so it is plain markup with no close control and
          no conditional rendering: there is no code path that hides it.
        */}
        <span className="rounded-sm border border-notice-line bg-notice-bg px-[10px] py-[6px] text-meta font-bold tracking-[.07em] text-notice">
          DATA SINTETIK
        </span>
      </div>
    </header>
  )
}
