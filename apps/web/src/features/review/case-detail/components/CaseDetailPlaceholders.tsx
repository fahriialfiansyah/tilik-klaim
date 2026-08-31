import { AlertTriangle, FileQuestion, RotateCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { withStop } from '@/features/review/shared/format'
import { ApiError } from '@/lib/http'

/**
 * The three states that all render as "a page with no case on it" and mean different things.
 *
 * Collapsing them is the same defect the queue's placeholders exist to avoid: a case that does
 * not exist and a service that did not answer lead to different next actions, and a reviewer
 * has no way to tell them apart from an empty screen.
 */

export function CaseDetailLoading() {
  return (
    <div className="px-[30px] py-[26px]" aria-busy="true" aria-live="polite">
      <span className="sr-only">Memuat detail kasus…</span>
      <div className="mb-[14px] h-[168px] animate-pulse rounded-lg border border-line bg-card" />
      <div className="grid gap-[14px] lg:grid-cols-[296px_minmax(0,1fr)_348px]">
        <div className="h-[280px] animate-pulse rounded-lg border border-line bg-card" />
        <div className="h-[420px] animate-pulse rounded-lg border border-line bg-card" />
        <div className="h-[520px] animate-pulse rounded-lg border border-line bg-card" />
      </div>
    </div>
  )
}

export function CaseDetailFailed({
  error,
  onRetry,
}: {
  readonly error: Error | null
  readonly onRetry: () => void
}) {
  const notFound = error instanceof ApiError && error.code === 'CASE_NOT_FOUND'
  const navigate = useNavigate()

  return (
    <div className="px-8 py-[72px] text-center">
      <div className="mb-[18px] flex justify-center text-ink-3">
        {notFound ? (
          <FileQuestion className="size-8" />
        ) : (
          <AlertTriangle className="size-8 text-band-conflict" />
        )}
      </div>
      <p className="mb-2 text-lead font-semibold">
        {notFound ? 'Kasus ini tidak ditemukan' : 'Detail kasus tidak dapat dimuat'}
      </p>
      <p className="mx-auto mb-5 max-w-[560px] text-body-lg text-ink-2 text-pretty">
        {notFound
          ? 'Pengenal kasus ini tidak ada dalam sistem. Kemungkinan tautannya sudah usang, atau basis data disaring ulang sejak tautan itu dibuat.'
          : `${withStop(error?.message ?? 'Layanan tidak merespons')} Ini bukan berarti kasusnya tidak ada — detailnya memang tidak sampai ke layar ini.`}
      </p>
      {notFound ? (
        <Button onClick={() => navigate('/')}>Kembali ke antrean</Button>
      ) : (
        <Button onClick={onRetry}>
          <RotateCw />
          Coba lagi
        </Button>
      )}
    </div>
  )
}
