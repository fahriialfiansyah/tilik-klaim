import { AlertTriangle, RotateCw, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'

/**
 * The states that all look like an empty table and mean different things.
 *
 * The same rule the queue follows: a blank table posing as "no accounts" while the service is
 * down is a lie the administrator has no way to detect.
 */
const SKELETON_ROWS = 3

export function UsersLoading() {
  return (
    <div className="p-4" aria-busy="true" aria-live="polite">
      <span className="sr-only">Memuat daftar pengguna…</span>
      {Array.from({ length: SKELETON_ROWS }, (_, index) => (
        <div key={index} className="flex items-center gap-3 border-b border-line py-[15px]">
          <span className="h-[13px] flex-1 animate-pulse rounded-sm bg-line" />
          <span className="h-[13px] w-[110px] animate-pulse rounded-sm bg-line" />
          <span className="h-[13px] w-[80px] animate-pulse rounded-sm bg-line" />
        </div>
      ))}
    </div>
  )
}

export function UsersEmpty() {
  return (
    <div className="px-8 py-[54px] text-center">
      <div className="mb-[18px] flex justify-center text-ink-3">
        <Users aria-hidden className="size-7" />
      </div>
      <p className="mb-2 text-lead font-semibold">Belum ada akun petugas</p>
      <p className="mx-auto max-w-[520px] text-body-lg text-ink-2 text-pretty">
        Basis data terjawab tetapi kosong. Tiga akun sintetik ditulis oleh{' '}
        <code className="font-mono text-body">scripts/seed_dev.py</code> — jalankan itu, lalu
        muat ulang halaman ini.
      </p>
    </div>
  )
}

export function UsersFailed({ onRetry }: { readonly onRetry: () => void }) {
  return (
    <div className="px-8 py-[54px] text-center">
      <div className="mb-[18px] flex justify-center text-ink-3">
        <AlertTriangle aria-hidden className="size-7" />
      </div>
      <p className="mb-2 text-lead font-semibold">Daftar pengguna tidak dapat dimuat</p>
      <p className="mx-auto mb-5 max-w-[520px] text-body-lg text-ink-2 text-pretty">
        Ini bukan berarti tidak ada pengguna. Layanan tidak menjawab, atau menolak permintaan
        ini.
      </p>
      <Button type="button" variant="outline" onClick={onRetry}>
        <RotateCw aria-hidden className="size-4" />
        Coba lagi
      </Button>
    </div>
  )
}
