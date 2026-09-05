import {
  ACTION_LABELS,
  RESOURCE_LABELS,
  actorLabel,
  auditKindLabel,
} from '@/features/review/case-detail/labels'
import type { AuditEvent } from '@/features/review/case-detail/types'
import type { LoadStatus } from '@/features/review/case-detail/useCaseDetail'
import { ExpandableText } from '@/features/review/shared/components/ExpandableText'
import { formatDateTime } from '@/features/review/shared/format'
import { STATE_LABELS } from '@/features/review/shared/labels'
import { cn } from '@/lib/utils'

/**
 * Widget 25 — the case history.
 *
 * Entries are appended and never rewritten, so a correction appears as a new event citing the
 * one it supersedes, with the superseded event still on screen. That is why the timeline shows
 * `supersedes_event_id` rather than quietly hiding the earlier decision: a history that edits
 * itself is not a history.
 */
export function AuditTimeline({
  caseId,
  events,
  status,
}: {
  readonly caseId: string
  readonly events: readonly AuditEvent[]
  readonly status: LoadStatus
}) {
  return (
    <section
      aria-label="Riwayat audit"
      className="max-w-[900px] rounded-lg border border-line bg-card p-[22px] shadow-panel"
    >
      <p className="mb-1 text-lead font-semibold">
        Riwayat audit kasus{' '}
        <span data-numeric className="font-mono">
          {caseId.replace(/^case_/, '').slice(0, 14)}
        </span>
      </p>
      <p className="mb-[22px] text-small text-ink-2 text-pretty">
        Setiap kejadian mencatat pelaku, tindakan, alasan, waktu, bukti yang dirujuk, dan versi
        mesin. Entri tidak pernah dihapus atau ditimpa.
      </p>

      {status === 'loading' ? (
        <p aria-busy="true" className="text-small text-ink-3">
          Memuat riwayat…
        </p>
      ) : null}

      {status === 'failed' ? (
        <p role="alert" className="text-small text-band-conflict">
          Riwayat tidak dapat dimuat. Ini bukan berarti kasus ini tidak punya riwayat; daftarnya
          memang tidak sampai ke layar ini.
        </p>
      ) : null}

      {status === 'ready' && events.length === 0 ? (
        <p className="text-small text-ink-3">
          Belum ada kejadian yang tercatat untuk kasus ini.
        </p>
      ) : null}

      <ol>
        {events.map((event, index) => (
          <li key={event.event_id} className="flex gap-4">
            <span
              data-numeric
              className="w-[128px] shrink-0 pt-[2px] font-mono text-meta text-ink-3"
            >
              {formatDateTime(event.occurred_at)}
            </span>
            <span aria-hidden className="flex shrink-0 flex-col items-center">
              <span
                className={cn(
                  'mt-[6px] size-[10px] rounded-full border-2 bg-card',
                  event.action ? 'border-brand' : 'border-line-strong',
                )}
              />
              {index < events.length - 1 ? <span className="w-px flex-1 bg-line" /> : null}
            </span>
            <span className="min-w-0 flex-1 pb-[22px]">
              <span className="block text-body font-semibold">
                {event.action ? ACTION_LABELS[event.action] : auditKindLabel(event.event_kind)}
              </span>
              <span className="mt-[3px] block text-small leading-relaxed text-ink-2 text-pretty">
                {actorLabel(event.actor_role)}
                {event.structured_reason ? ` · ${event.structured_reason}` : ''}
                {event.state_before && event.state_after
                  ? ` · ${STATE_LABELS[event.state_before]} → ${STATE_LABELS[event.state_after]}`
                  : ''}
              </span>
              {event.note ? (
                <span className="mt-[6px] block rounded-md border border-line bg-sunk px-3 py-2 text-small">
                  <ExpandableText text={event.note} className="text-pretty" />
                </span>
              ) : null}
              {event.evidence.length > 0 ? (
                <span className="mt-[6px] block text-meta text-ink-3">
                  Bukti diminta:{' '}
                  {event.evidence
                    .map((ref) => RESOURCE_LABELS[ref.resource_type] ?? ref.resource_type)
                    .join(', ')}
                </span>
              ) : null}
              <span data-numeric className="mt-[5px] block font-mono text-micro text-ink-3">
                {auditKindLabel(event.event_kind)} · aturan v
                {event.versions.ruleset_version} · mesin v{event.versions.engine_version}
                {event.supersedes_event_id
                  ? ` · menggantikan ${event.supersedes_event_id.slice(0, 8)}`
                  : ''}
              </span>
            </span>
          </li>
        ))}
      </ol>
    </section>
  )
}
