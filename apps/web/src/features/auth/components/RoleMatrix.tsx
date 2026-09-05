import { Check, X } from 'lucide-react'

import { DEMO_ACCOUNTS, type DemoAccount } from '@/features/auth/accounts'
import { ROLE_LABEL } from '@/features/auth/labels'
import { MATRIX_COLUMNS, allows } from '@/features/auth/matrix'
import type { Role } from '@/features/auth/types'
import { cn } from '@/lib/utils'

/**
 * The access matrix, used as the persona picker.
 *
 * Rows are the three synthetic staff, columns are what each may do, and choosing a row chooses
 * who you sign in as. Anyone reading it learns the role model before they have signed in —
 * which is the separation of duties `07_privacy_threat_model.md` names, made visible instead of
 * described.
 *
 * **Selection is a real radio group inside a real table.** Each row's first cell holds an
 * `<input type="radio">` whose label covers the row, so arrow keys move between personas, the
 * group has one tab stop, and assistive technology announces both the person and the cell
 * headings — none of which a `<div>` with `role="radio"` would give for free.
 *
 * **Colour never carries the answer alone.** Every cell says *Boleh* or *Tidak* in words; the
 * tick and cross are decorative and hidden from assistive technology, which reads the word.
 */
const ROLE_ACCENT: Readonly<Record<Role, string>> = {
  reviewer: 'bg-band-context-bg border-band-context-line text-band-context',
  senior_reviewer: 'bg-band-signal-bg border-band-signal-line text-band-signal',
  admin: 'bg-brand-soft border-brand-line text-brand',
}

export function RoleMatrix({
  chosen,
  onChoose,
}: {
  readonly chosen: DemoAccount
  readonly onChoose: (account: DemoAccount) => void
}) {
  return (
    <div className="overflow-hidden rounded-md border border-line bg-card">
      <table className="w-full border-collapse text-left">
        <caption className="sr-only">
          Akun contoh dan kemampuan tiap peran. Pilih satu baris untuk masuk sebagai orang itu.
        </caption>
        <thead>
          <tr className="bg-sunk">
            <th
              scope="col"
              className="border-b border-line px-4 py-[10px] font-mono text-micro font-semibold uppercase tracking-label text-ink-3"
            >
              Akun contoh
            </th>
            {MATRIX_COLUMNS.map((column) => (
              <th
                key={column.key}
                scope="col"
                className="border-b border-line px-2 py-[10px] text-center align-bottom font-mono text-micro font-semibold uppercase leading-[1.35] tracking-label text-ink-3"
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {DEMO_ACCOUNTS.map((account) => {
            const isChosen = account.staffCode === chosen.staffCode
            return (
              <tr
                key={account.staffCode}
                className={cn('border-b border-line last:border-b-0', isChosen && 'bg-brand-soft')}
              >
                <th scope="row" className="px-4 py-4 font-normal">
                  <label className="flex cursor-pointer items-center gap-3">
                    <input
                      type="radio"
                      name="persona"
                      value={account.staffCode}
                      checked={isChosen}
                      onChange={() => onChoose(account)}
                      className="size-4 shrink-0 accent-[var(--a-1)]"
                    />
                    <span
                      className={cn(
                        'shrink-0 rounded-md border px-[9px] py-[2px] text-small font-semibold',
                        ROLE_ACCENT[account.role],
                      )}
                    >
                      {ROLE_LABEL[account.role]}
                    </span>
                    <span className="min-w-0">
                      <span className="block truncate text-body font-semibold text-ink">
                        {account.fullName}
                      </span>
                      <span data-numeric className="block font-mono text-meta text-ink-3">
                        {account.staffCode}
                      </span>
                    </span>
                  </label>
                </th>

                {MATRIX_COLUMNS.map((column) => {
                  const permitted = allows(account.role, column.key)
                  return (
                    <td key={column.key} className="px-2 py-4 text-center">
                      <span
                        className={cn(
                          'inline-flex items-center gap-[5px] text-meta font-semibold',
                          permitted ? 'text-brand' : 'text-ink-3',
                        )}
                      >
                        {permitted ? (
                          <Check aria-hidden className="size-[13px]" />
                        ) : (
                          <X aria-hidden className="size-[13px]" />
                        )}
                        {permitted ? 'Boleh' : 'Tidak'}
                      </span>
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
