import { Trans, useTranslation } from 'react-i18next'

import { AlertTriangle, ArrowRight, Info, RotateCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { shortHash } from '@/features/review/ingest/hash'
import { withStop } from '@/features/review/shared/format'

/**
 * Widget 7 — the completeness notes, on their own banner.
 *
 * This is the distinction the whole module exists to protect. An incomplete record and a
 * billed-but-unevidenced service look identical at the schema level; conflating them is how
 * this system would manufacture a false accusation. So the notes say plainly what absence
 * *means* here — lower certainty and a request for documents, never a stronger signal —
 * because the amber alone would read as "something is wrong with this claim".
 */
export function CompletenessBanner({ notes }: { readonly notes: readonly string[] }) {
  const { t } = useTranslation('ingest')

  return (
    <div
      role="note"
      className="mb-[14px] rounded-lg border border-notice-line bg-notice-bg px-4 py-[14px]"
    >
      <p className="mb-2 flex items-start gap-3 text-small leading-relaxed text-pretty">
        <AlertTriangle aria-hidden className="mt-[2px] size-4 shrink-0 text-notice" />
        <span>
          <span className="font-semibold text-notice">{t('banner.completenessTitle')}</span>
          <Trans
            i18nKey="banner.completenessBody"
            ns="ingest"
            components={[<span key="0" />, <strong key="1" />]}
          />
        </span>
      </p>
      <ul className="ms-[28px] space-y-1">
        {notes.map((note) => (
          <li key={note} className="text-small text-ink-2">
            · {note}
          </li>
        ))}
      </ul>
    </div>
  )
}

/**
 * Widget 10 — the same bundle has been here before.
 *
 * Re-submitting identical content does **not** produce a second case: the idempotency key folds
 * the content hash together with the engine and ruleset versions, so the store returns the
 * record that exists. `brief/01_INGEST_VALIDASI.md` § 4.2 calls this out as a demo requirement
 * — pressing the button twice must not put twin cases in the queue.
 */
export function DuplicateBanner({
  caseId,
  inputHash,
}: {
  readonly caseId: string
  readonly inputHash: string
}) {
  const { t } = useTranslation('ingest')
  const navigate = useNavigate()
  return (
    <div
      role="note"
      className="mb-[14px] flex items-start gap-[14px] rounded-lg border border-brand-line bg-brand-soft px-4 py-[14px]"
    >
      <Info aria-hidden className="mt-[2px] size-[18px] shrink-0 text-brand" />
      <div className="min-w-0 flex-1">
        <p className="mb-[3px] font-semibold">
          {t('banner.duplicateTitle')}
        </p>
        <p className="text-small leading-relaxed text-ink-2 text-pretty">
          <Trans
            i18nKey="banner.duplicateBody"
            ns="ingest"
            values={{ hash: shortHash(inputHash) }}
            components={[<span key="0" data-numeric className="font-mono" />]}
          />
        </p>
      </div>
      <Button
        variant="outline"
        size="sm"
        className="shrink-0"
        onClick={() => navigate(`/cases/${encodeURIComponent(caseId)}`)}
      >
        {t('banner.openCase')}
        <ArrowRight />
      </Button>
    </div>
  )
}

/**
 * Widget 11 — the service did not answer.
 *
 * Never a spinner that resolves into nothing: `brief/01_INGEST_VALIDASI.md` § 8 names the
 * hanging loading state as the failure to avoid, because an operator cannot tell it apart from
 * a slow success and will eventually press the button again.
 */
export function ServiceErrorBanner({
  title,
  error,
  onRetry,
}: {
  readonly title: string
  readonly error: Error | null
  readonly onRetry: () => void
}) {
  const { t } = useTranslation(['ingest', 'common'])
  return (
    <div
      role="alert"
      className="mb-[14px] flex items-start gap-[14px] rounded-lg border border-band-conflict-line bg-band-conflict-bg px-4 py-[14px]"
    >
      <AlertTriangle aria-hidden className="mt-[2px] size-[18px] shrink-0 text-band-conflict" />
      <div className="min-w-0 flex-1">
        <p className="mb-[3px] font-semibold text-band-conflict">{title}</p>
        <p className="text-small leading-relaxed text-ink-2 text-pretty">
          {t('ingest:banner.serviceBody', {
            detail: withStop(error?.message ?? t('ingest:banner.serviceDown')),
          })}
        </p>
      </div>
      <Button variant="outline" size="sm" className="shrink-0" onClick={onRetry}>
        <RotateCw />
        {t('common:action.retry')}
      </Button>
    </div>
  )
}

/**
 * The context carried in from a case's "minta bukti tambahan".
 *
 * `/cases/:id` navigates here with `?case=<id>` after that action, per `brief/04` § 3.1. Saying
 * so is the whole of the requirement — the operator arrived with a case in mind and needs to
 * see that the screen knows it, and a way back if they navigated here by accident.
 */
export function EvidenceRequestBanner({ caseId }: { readonly caseId: string }) {
  const { t } = useTranslation('ingest')
  const navigate = useNavigate()
  return (
    <div
      role="note"
      className="mb-[14px] flex items-start gap-[14px] rounded-lg border border-brand-line bg-brand-soft px-4 py-[14px]"
    >
      <Info aria-hidden className="mt-[2px] size-[18px] shrink-0 text-brand" />
      <div className="min-w-0 flex-1">
        <p className="mb-[3px] font-semibold">{t('banner.evidenceRequestTitle')}</p>
        <p className="text-small leading-relaxed text-ink-2 text-pretty">
          {t('banner.evidenceRequestBody')}
        </p>
      </div>
      <Button
        variant="outline"
        size="sm"
        className="shrink-0"
        onClick={() => navigate(`/cases/${encodeURIComponent(caseId)}`)}
      >
        {t('banner.openCase')}
        <ArrowRight />
      </Button>
    </div>
  )
}
