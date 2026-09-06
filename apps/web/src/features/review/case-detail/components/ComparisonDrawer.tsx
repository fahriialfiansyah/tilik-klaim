import { useTranslation } from 'react-i18next'

import { AlertTriangle } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Dialog, DialogContent } from '@/components/ui/dialog'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { componentLabel } from '@/features/review/case-detail/labels'
import type { ComparisonCandidate } from '@/features/review/case-detail/types'
import { formatDateRange, formatIfTimestamp } from '@/features/review/shared/format'
import { useLastPresent } from '@/lib/useLastPresent'
import { cn } from '@/lib/utils'

/**
 * Widgets 23 and 24 — the two candidates side by side, and the template warning.
 *
 * Two constraints shape what is on screen.
 *
 * **The highlight must not identify anyone.** For cloned documentation the pair spans two
 * participants by definition, so the API sends the peer note's *shape* — kind, timing, length,
 * digest — and never its text or its owner. `docs/canonical/07_privacy_threat_model.md` names
 * the similarity highlight as the exposure route, which is why nothing here reassembles a
 * fuller picture from what it was given.
 *
 * **Matching and differing fields are drawn differently, and both are labelled.** A reviewer
 * deciding whether two claims are one service or two is reading the differences; showing them
 * only as a colour would put the answer behind a perception the page cannot rely on.
 */
export function ComparisonDrawer({
  candidate,
  onClose,
}: {
  readonly candidate: ComparisonCandidate | null
  readonly onClose: () => void
}) {
  // Kept for the closing frame so Radix can return focus to the button that opened this.
  const { t } = useTranslation('caseDetail')
  const shown = useLastPresent(candidate)

  return (
    <Dialog open={candidate !== null} onOpenChange={(open) => !open && onClose()}>
      {shown ? (
        <DialogContent
          variant="drawer"
          title={t('comparison.title')}
          description={t('comparison.description')}
        >
          <PerfectScrollArea className="flex-1 px-5 py-4">
            {/*
              The caveat sits at the top of the drawer, before any field and before any action —
              `brief/04_DETAIL_KASUS_DISPOSISI.md` § 2.4 requires it to be read first, because a
              high similarity score with no context invites exactly the wrong conclusion.
            */}
            {shown.template_caveat ? (
              <div
                role="note"
                className="mb-5 flex gap-3 rounded-md border border-notice-line bg-notice-bg px-4 py-3"
              >
                <AlertTriangle aria-hidden className="mt-[2px] size-4 shrink-0 text-notice" />
                <p className="text-small leading-relaxed text-pretty">
                  <span className="font-semibold text-notice">{t('banner.templateCaveat')}</span>
                  {shown.template_caveat}
                </p>
              </div>
            ) : null}

            {/*
              The way in. The drawer names the candidate claim; without a route to its own case
              a reviewer had to go back to the queue and find it by hand — on the screen that is
              most expensive to misread. `candidate_case_id` is null when the candidate was
              accepted but never screened, so there is genuinely no case to open, and when the
              candidate is another participant's note: cloning crosses that boundary, and the
              service is handed the note rather than the submission behind it.
            */}
            <p className="mb-[10px] flex flex-wrap items-baseline gap-x-2 gap-y-1 text-small">
              <span className="font-mono text-micro font-semibold tracking-label text-ink-3">
                {t('comparison.candidate')}
              </span>
              <span className="font-mono text-ink">{shown.candidate_claim_id}</span>
              {shown.candidate_case_id ? (
                <Link
                  to={`/cases/${shown.candidate_case_id}`}
                  onClick={onClose}
                  className="text-brand underline underline-offset-2"
                >
                  {t('comparison.openCandidate')}
                </Link>
              ) : (
                <span className="text-ink-2">{t('comparison.noCandidateCase')}</span>
              )}
            </p>

            <p className="mb-[10px] font-mono text-micro font-semibold tracking-label text-ink-3">
              {t('comparison.fieldsHeading')}
            </p>
            <table className="mb-6 w-full border-collapse text-small">
              <thead>
                <tr>
                  <th scope="col" className="w-[132px] border-b border-line py-2 text-left text-ink-3 font-mono text-micro tracking-label">
                    {t('comparison.field')}
                  </th>
                  <th scope="col" className="border-b border-line py-2 text-left text-ink-3 font-mono text-micro tracking-label">
                    {t('comparison.thisCase')}
                  </th>
                  <th scope="col" className="border-b border-line py-2 text-left text-ink-3 font-mono text-micro tracking-label">
                    {t('comparison.candidate')}
                  </th>
                  <th scope="col" className="w-[80px] border-b border-line py-2 text-left text-ink-3 font-mono text-micro tracking-label">
                    {t('comparison.state')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {shown.fields.map((field) => (
                  <tr key={field.field_name} className="border-b border-line">
                    <th scope="row" className="py-[9px] pe-3 text-left font-medium text-ink-2">
                      {field.field_name}
                    </th>
                    <td
                      data-numeric
                      className={cn(
                        'py-[9px] pe-3 break-words',
                        !field.matches && 'font-medium text-band-signal',
                      )}
                    >
                      {formatIfTimestamp(field.left_value)}
                    </td>
                    <td
                      data-numeric
                      className={cn(
                        'py-[9px] pe-3 break-words',
                        !field.matches && 'font-medium text-band-signal',
                      )}
                    >
                      {formatIfTimestamp(field.right_value)}
                    </td>
                    <td className="py-[9px] text-meta text-ink-3">
                      {field.matches ? 'cocok' : 'berbeda'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <p className="mb-[10px] font-mono text-micro font-semibold tracking-label text-ink-3">
              {t('comparison.overlapHeading')}
            </p>
            <p className="mb-6 text-small text-ink-2">
              {shown.overlap_start
                ? formatDateRange(shown.overlap_start, shown.overlap_end)
                : t('comparison.noOverlap')}
            </p>

            <p className="mb-[10px] font-mono text-micro font-semibold tracking-label text-ink-3">
              {t('comparison.similarityHeading')}
            </p>
            <dl className="mb-2">
              {Object.entries(shown.similarity_components).map(([name, value]) => (
                <div key={name} className="flex gap-4 border-t border-line py-[9px] text-small">
                  <dt className="w-[196px] shrink-0 text-ink-3">{componentLabel(name)}</dt>
                  <dd data-numeric className="font-medium">
                    {value}
                  </dd>
                </div>
              ))}
            </dl>
          </PerfectScrollArea>
        </DialogContent>
      ) : null}
    </Dialog>
  )
}
