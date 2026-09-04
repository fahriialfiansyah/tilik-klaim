import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import { BrandPanel } from '@/features/auth/components/BrandPanel'
import { SignInForm } from '@/features/auth/components/SignInForm'
import { LANDING_ROUTE } from '@/features/auth/permissions'
import { useSession } from '@/features/auth/useSession'
import { ThemeToggle } from '@/modules/theme/ThemeToggle'

/**
 * `/login` — the only route outside `AppShell`.
 *
 * A split layout: the mark at size on the header's dark navy, and the form on the card surface.
 * The impact is meant to come from hierarchy, spacing, and one piece of motion that means
 * something — `design/DESIGN.md` locks the direction against neon gradients and chatbot effects,
 * and a login page that broke it would undercut the product's own credibility argument in front
 * of the people this page is first shown to.
 *
 * Two badges, neither dismissible: `AKUN SIMULASI` because the sign-in selects a persona rather
 * than authenticating anyone (ADR-0006 § 3), and `DATA SINTETIK` because
 * `07_privacy_threat_model.md` requires it on every page.
 */
export function LoginPage() {
  const navigate = useNavigate()
  const user = useSession((state) => state.user)

  useEffect(() => {
    document.title = 'Masuk — TilikKlaim'
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
    <div className="min-h-screen bg-background lg:grid lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <BrandPanel />

      <main className="flex flex-col gap-8 px-6 py-8 sm:px-10 lg:px-14 lg:py-14">
        <div className="flex flex-wrap items-center justify-end gap-[10px]">
          <ThemeToggle />
          {/*
            Neither badge has a close control and neither is conditionally rendered: there is no
            code path that hides them, which is what "tidak dapat ditutup" has to mean to be true.
          */}
          <span className="rounded-sm border border-brand-line bg-brand-soft px-[10px] py-[6px] text-meta font-bold tracking-[.07em] text-brand">
            AKUN SIMULASI
          </span>
          <span className="rounded-sm border border-notice-line bg-notice-bg px-[10px] py-[6px] text-meta font-bold tracking-[.07em] text-notice">
            DATA SINTETIK
          </span>
        </div>

        <div className="w-full max-w-[560px]">
          <SignInForm />
        </div>
      </main>
    </div>
  )
}
