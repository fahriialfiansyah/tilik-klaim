import { Trans, useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Dialog, DialogClose, DialogContent } from '@/components/ui/dialog'

/**
 * Widget 26 — the confirmation that stands between confirming an anomaly and a permanent record.
 *
 * It exists to say one thing plainly: **this is not a fraud finding.** The action means a
 * reviewer agrees an inconsistency exists and should be followed up. It rejects no claim, stops
 * no payment, imposes no sanction, and changes no code — `docs/canonical/01_product_decision.md`
 * puts all four out of scope, and the backend's disposition service has no path to any of them.
 *
 * Cancelling returns to the panel with nothing changed, so a reviewer who reads this and
 * reconsiders loses none of their work.
 */
export function ConfirmAnomalyDialog({
  open,
  onOpenChange,
  onConfirm,
  structuredReason,
}: {
  readonly open: boolean
  readonly onOpenChange: (open: boolean) => void
  readonly onConfirm: () => void
  readonly structuredReason: string
}) {
  const { t } = useTranslation(['caseDetail', 'common'])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        title={t('caseDetail:confirmAnomaly.title')}
        description={t('caseDetail:confirmAnomaly.description')}
      >
        <div className="px-5 py-4">
          <p className="mb-3 text-small leading-relaxed text-pretty">
            <Trans
              i18nKey="confirmAnomaly.lede"
              ns="caseDetail"
              components={[<span key="0" />, <strong key="1" />, <span key="2" />, <strong key="3" />]}
            />
          </p>
          <ul className="mb-4 space-y-1 rounded-md border border-line bg-sunk px-4 py-3 text-small text-ink-2">
            <li>{t('caseDetail:confirmAnomaly.point1')}</li>
            <li>{t('caseDetail:confirmAnomaly.point2')}</li>
            <li>{t('caseDetail:confirmAnomaly.point3')}</li>
            <li>{t('caseDetail:confirmAnomaly.point4')}</li>
          </ul>
          <p className="mb-5 text-small text-ink-2 text-pretty">
            {t('caseDetail:confirmAnomaly.reasonRecorded')}
            <strong className="text-ink">{structuredReason}</strong>
          </p>

          <div className="flex justify-end gap-2">
            <DialogClose asChild>
              <Button variant="outline">{t('common:action.cancel')}</Button>
            </DialogClose>
            <Button onClick={onConfirm}>{t('caseDetail:confirmAnomaly.confirm')}</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
