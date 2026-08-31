import { AlertTriangle } from 'lucide-react'
import { useRef, useState } from 'react'

import {
  ACCEPT_ATTRIBUTE,
  ACCEPTED_EXTENSIONS,
  MAX_BUNDLE_BYTES,
  MAX_JSON_DEPTH,
  formatBytes,
} from '@/features/review/ingest/limits'
import { cn } from '@/lib/utils'

/**
 * Widgets 1 and 2 — the drop zone, and the limits stated before an upload rather than after a
 * failure.
 *
 * The limits sit **under the zone, always visible**, not behind a tooltip or an error. That is
 * `brief/01_INGEST_VALIDASI.md` § 2.1: an operator should learn the file is too big before
 * spending a minute uploading it, and should be told the actual number when it is.
 *
 * The real control is an `<input type="file">` inside a label, so the keyboard and assistive
 * tech get the browser's own file picker. Drag-and-drop is layered on top of that rather than
 * replacing it — a drop zone with no focusable input is unusable without a pointer.
 */
export function UploadZone({
  onFile,
  rejection,
  isBusy,
}: {
  readonly onFile: (file: File) => void
  readonly rejection: string | null
  readonly isBusy: boolean
}) {
  const [isDragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const take = (files: FileList | null) => {
    const file = files?.[0]
    if (file) {
      onFile(file)
    }
  }

  return (
    <div>
      <label
        onDragOver={(event) => {
          event.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          take(event.dataTransfer.files)
        }}
        className={cn(
          'block cursor-pointer rounded-lg border-[1.5px] border-dashed px-6 py-[34px] text-center transition-colors',
          isDragging ? 'border-brand bg-brand-soft' : 'border-line-strong bg-sunk',
          isBusy && 'pointer-events-none opacity-60',
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT_ATTRIBUTE}
          disabled={isBusy}
          onChange={(event) => {
            take(event.target.files)
            // Cleared so choosing the same file twice fires `change` again — otherwise a retry
            // after a failed submission silently does nothing.
            event.target.value = ''
          }}
          className="sr-only"
        />
        <span aria-hidden className="mb-[14px] flex justify-center gap-1">
          <span className="h-[5px] w-[26px] rounded-sm bg-line-strong" />
          <span className="h-[5px] w-10 rounded-sm bg-brand" />
          <span className="h-[5px] w-[18px] rounded-sm bg-line-strong" />
        </span>
        <span className="mb-1 block text-body-lg font-semibold">
          Seret berkas bundel ke sini
        </span>
        <span className="mb-[14px] block text-small text-ink-2">
          Satu berkas data terstruktur per pemasukan
        </span>
        <span className="inline-block rounded-md bg-brand px-[17px] py-[9px] text-small font-semibold text-brand-on">
          Pilih berkas
        </span>
      </label>

      {/* Widget 2 — before the upload, not after the failure. */}
      <dl className="mt-[14px] flex flex-wrap gap-x-4 gap-y-1 text-meta text-ink-3">
        <div className="flex gap-1">
          <dt>Ukuran maksimum</dt>
          <dd data-numeric className="font-semibold text-ink">
            {formatBytes(MAX_BUNDLE_BYTES)}
          </dd>
        </div>
        <div className="flex gap-1">
          <dt>Tipe</dt>
          <dd className="font-semibold text-ink">
            bundel klaim ({ACCEPTED_EXTENSIONS.join(', ')})
          </dd>
        </div>
        <div className="flex gap-1">
          <dt>Kedalaman maksimum</dt>
          <dd data-numeric className="font-semibold text-ink">
            {MAX_JSON_DEPTH}
          </dd>
        </div>
      </dl>

      {rejection ? (
        <p
          role="alert"
          className="mt-3 flex items-start gap-[10px] rounded-md border border-band-conflict-line bg-band-conflict-bg px-[13px] py-[10px] text-small"
        >
          <AlertTriangle aria-hidden className="mt-[2px] size-4 shrink-0 text-band-conflict" />
          <span className="text-pretty">{rejection}</span>
        </p>
      ) : null}
    </div>
  )
}
