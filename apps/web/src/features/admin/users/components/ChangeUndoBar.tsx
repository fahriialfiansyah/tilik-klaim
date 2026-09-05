import { RotateCcw, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import type { UndoableChange } from '@/features/admin/users/useUsers'

/**
 * What just happened, and one way back.
 *
 * **Undo appends a reversing change; it never removes the original.** The strip says so, because
 * "Urungkan" beside an append-only trail is a word that can be read two ways, and the wrong
 * reading is the one that makes this page look like it can rewrite its own history.
 *
 * `role="status"` rather than `role="alert"`: this is a confirmation of something the
 * administrator just did on purpose, not an interruption, so it is announced without stealing
 * focus from the row they are still working in.
 */
export function ChangeUndoBar({
  change,
  busy,
  onUndo,
  onDismiss,
}: {
  readonly change: UndoableChange
  readonly busy: boolean
  readonly onUndo: () => void
  readonly onDismiss: () => void
}) {
  return (
    <div
      role="status"
      className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-md border border-line bg-sunk px-4 py-3"
    >
      <p className="min-w-0 flex-1 text-body text-ink text-pretty">
        <span className="font-semibold">Tersimpan: </span>
        {change.summary}{' '}
        <span className="text-meta text-ink-3">
          Mengurungkan akan mencatat perubahan balik; catatan aslinya tetap ada.
        </span>
      </p>
      <span className="flex shrink-0 items-center gap-2">
        <Button type="button" variant="outline" disabled={busy} onClick={onUndo}>
          <RotateCcw aria-hidden className="size-4" />
          Urungkan
        </Button>
        <Button
          type="button"
          variant="outline"
          aria-label="Tutup pemberitahuan"
          disabled={busy}
          onClick={onDismiss}
        >
          <X aria-hidden className="size-4" />
        </Button>
      </span>
    </div>
  )
}
