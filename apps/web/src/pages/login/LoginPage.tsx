import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { TilikKlaimMark } from '@/components/brand/TilikKlaimMark'
import { ClaimTexture } from '@/features/auth/components/ClaimTexture'
import { SignInForm } from '@/features/auth/components/SignInForm'
import { LANDING_ROUTE } from '@/features/auth/permissions'
import { useSession } from '@/features/auth/useSession'
import { ThemeToggle } from '@/modules/theme/ThemeToggle'

const MARK_DRAW_MS = 700

/**
 * `/login` — the only route outside `AppShell`, and the whole of it fits one screen.
 *
 * **The page is the access matrix.** Choosing a row chooses who you sign in as, so a judge
 * learns the role model — three roles, and an administrator who never touches a claim — before
 * they have signed in at all. `07_privacy_threat_model.md` § Governance deliverables already
 * owed a "Role/access matrix"; this is that deliverable, alive rather than filed.
 *
 * **It claims nothing about security.** A permanent `AKUN SIMULASI` badge sits beside the
 * existing `DATA SINTETIK` one, the passcodes are printed on screen, and the copy says the
 * sign-in selects a persona. ADR-0006 § 3 is why, and its first kill criterion is this page
 * being read as a security claim by any non-domain reader.
 *
 * **The background is generated from the product's own data shape** — claim lines, evidence
 * connectors, and rare amber gaps — rather than from anyone else's imagery. The competition's
 * originality rule forbids using intellectual property that is not ours, and that includes the
 * organiser's; the footer says plainly that this is not an official BPJS Kesehatan product.
 *
 * Height is locked to the viewport (`h-svh` + `overflow-hidden`): a login that scrolls is the
 * first thing a judge sees not fitting on screen.
 */
export function LoginPage() {
  const navigate = useNavigate()
  const user = useSession((state) => state.user)
  const [drawn, setDrawn] = useState(false)

  useEffect(() => {
    document.title = 'Masuk · TilikKlaim'
  }, [])

  useEffect(() => {
    // The mark strokes itself in once: an evidence chain closing into a loop, which is what the
    // product does. Respects `prefers-reduced-motion` by simply being complete on the first frame.
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
    if (reduced) {
      setDrawn(true)
      return
    }
    const handle = window.requestAnimationFrame(() => setDrawn(true))
    return () => window.cancelAnimationFrame(handle)
  }, [])

  useEffect(() => {
    // Covers both arrivals: a successful sign-in, and someone already signed in reaching
    // /login by URL — who is sent where their role works rather than offered a sign-in that
    // would replace a session they never asked to end.
    if (user) {
      navigate(LANDING_ROUTE[user.role], { replace: true })
    }
  }, [user, navigate])

  return (
    <div className="flex h-svh flex-col overflow-hidden bg-background">
      <header className="flex h-[var(--header-h)] shrink-0 items-center justify-between gap-4 bg-head px-6">
        <div className="flex items-center gap-[10px]">
          <TilikKlaimMark className="block size-[26px] shrink-0" />
          <span className="text-lead font-semibold tracking-[.11em] text-ink-inv">TILIKKLAIM</span>
        </div>
        <div className="flex items-center gap-[10px]">
          <ThemeToggle />
          {/*
            Neither badge has a close control and neither is conditionally rendered: there is no
            code path that hides them, which is what "tidak dapat ditutup" has to mean to be true.
          */}
          {/*
            Two badges, told apart on purpose: the brand teal marks *who* is signed in as being
            simulated, the amber marks the *data*. One colour for both would read as a single
            disclaimer rather than two separate facts.
          */}
          <span className="rounded-sm border border-brand-line bg-brand-soft px-[10px] py-[6px] text-meta font-bold tracking-[.07em] text-brand">
            AKUN SIMULASI
          </span>
          <span className="rounded-sm border border-notice-line bg-notice-bg px-[10px] py-[6px] text-meta font-bold tracking-[.07em] text-notice">
            DATA SINTETIK
          </span>
        </div>
      </header>

      <main className="relative flex min-h-0 flex-1 flex-col justify-center gap-6 px-6 py-6 lg:px-12">
        <ClaimTexture className="pointer-events-none absolute inset-0 h-full w-full text-ink-3 opacity-[0.24]" />

        <div className="relative flex items-end justify-between gap-8">
          <div>
            <h1 className="text-page font-semibold tracking-title text-ink text-pretty">
              Pilih peran Anda hari ini
            </h1>
            <p className="mt-2 max-w-[62ch] text-body leading-[1.6] text-ink-2 text-pretty">
              Halaman ini <strong className="font-semibold text-ink">memilih peran</strong> untuk
              prototipe. Ia tidak mengamankan apa pun: kode demo tertera di bawah dan disimpan apa
              adanya. Penegakan akses tingkat perusahaan tercatat sebagai kebutuhan produksi, bukan
              fitur yang sudah dibangun.
            </p>
          </div>
          <TilikKlaimMark
            className="hidden size-[112px] shrink-0 text-ink-2 lg:block"
            drawn={drawn}
            drawMs={MARK_DRAW_MS}
            onSurface
          />
        </div>

        <div className="relative">
          <SignInForm />
        </div>

        <div className="relative flex flex-wrap items-baseline justify-between gap-x-8 gap-y-2">
          <p className="font-mono text-micro tracking-label text-ink-3">
            HEALTHKATHON 2026 ·{' '}
            <span className="font-semibold text-ink-2">
              KATEGORI 2: EFISIENSI RISIKO PADA FASILITAS KESEHATAN
            </span>
          </p>
          <p className="text-meta text-ink-3">
            Kolom bertanda <strong className="font-semibold text-ink-2">Tidak</strong> ditolak oleh
            server dengan kode galat tetap; menyembunyikan tombol bukan kendali akses. Matriks
            lengkap ada di ADR-0006 § 2. Prototipe fungsional dari tim peserta,{' '}
            <strong className="font-semibold text-ink-2">
              bukan produk atau layanan resmi BPJS Kesehatan.
            </strong>
          </p>
        </div>
      </main>
    </div>
  )
}
