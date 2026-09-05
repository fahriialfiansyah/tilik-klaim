import { Button } from '@/components/ui/button'
import { Dialog, DialogClose, DialogContent } from '@/components/ui/dialog'

/**
 * Widget 26 — the confirmation that stands between "konfirmasi anomali" and a permanent record.
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
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        title="Konfirmasi anomali: ini bukan temuan fraud"
        description="Bacalah penegasan ini sebelum keputusan dicatat permanen."
      >
        <div className="px-5 py-4">
          <p className="mb-3 text-small leading-relaxed text-pretty">
            Menekan konfirmasi berarti Anda membenarkan adanya{' '}
            <strong>ketidaksesuaian yang perlu ditindaklanjuti</strong>. Itu saja. Tindakan ini{' '}
            <strong>bukan</strong> pernyataan fraud, bukan temuan hukum, dan bukan tuduhan
            terhadap pihak mana pun.
          </p>
          <ul className="mb-4 space-y-1 rounded-md border border-line bg-sunk px-4 py-3 text-small text-ink-2">
            <li>· Klaim tidak ditolak.</li>
            <li>· Pembayaran tidak dihentikan dan tidak diubah.</li>
            <li>· Tidak ada sanksi yang dijatuhkan.</li>
            <li>· Tidak ada kode yang diubah.</li>
          </ul>
          <p className="mb-5 text-small text-ink-2 text-pretty">
            Alasan yang akan tercatat: <strong className="text-ink">{structuredReason}</strong>
          </p>

          <div className="flex justify-end gap-2">
            <DialogClose asChild>
              <Button variant="outline">Batal</Button>
            </DialogClose>
            <Button onClick={onConfirm}>Saya paham, catat konfirmasi</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
