import type { ComponentType } from 'react'

/**
 * One drawn mark per navigable page.
 *
 * Each says what its page *holds*, not what its page is called, so the pair reads faster than
 * either alone: a sorted work list, a bundle arriving, measured bars, a roster. They are the
 * icon vocabulary `design/DESIGN.md` allows — evidence, time, links, documents, human review —
 * and none of them is a robot head or a sparkle, which that file forbids by name.
 *
 * Drawn here rather than taken from an icon set for two reasons. A generic "list" and a generic
 * "chart" would describe any dashboard; these describe *these* pages. And the stroke weight,
 * cap and radius match `TilikKlaimMark`, which is the only other line-work in the shell.
 *
 * All four are `aria-hidden`: the menu label beside them carries the meaning, and an icon that
 * repeated it would make every entry announce itself twice.
 */
export type MenuIcon = ComponentType<{ readonly className?: string }>

const SVG_PROPS = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.75,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
} as const

/**
 * Antrean Review — a work list with a priority rail down its left edge.
 *
 * The rail is the queue's own device: `BAND_RAIL` draws exactly this 3 px bar beside every row.
 * Rows are uneven because the queue is sorted, not because the drawing needed variety.
 */
export function QueueIcon({ className }: { readonly className?: string }) {
  return (
    <svg aria-hidden className={className} {...SVG_PROPS}>
      <path d="M3.75 5.5v13" strokeWidth="2.5" />
      <path d="M8.5 7h11.75M8.5 12h8.25M8.5 17h10" />
    </svg>
  )
}

/**
 * Ingest / Demo — a bundle arriving in a tray.
 *
 * An arrow *into* something, because this page is the one place data enters the system. The
 * tray's notch is where a submitted bundle lands.
 */
export function IngestIcon({ className }: { readonly className?: string }) {
  return (
    <svg aria-hidden className={className} {...SVG_PROPS}>
      <path d="M12 3v7.5" />
      <path d="m8.75 7.5 3.25 3.25L15.25 7.5" />
      <path d="M3.75 13.5h4.5l1.5 2.25h4.5l1.5-2.25h4.5v4.25a2 2 0 0 1-2 2H5.75a2 2 0 0 1-2-2z" />
    </svg>
  )
}

/**
 * Audit & Evaluasi — three measured bars standing on a baseline.
 *
 * The baseline is the point: this page reports numbers against a fixed reference, and a bar
 * without an axis is a shape rather than a measurement.
 */
export function EvaluationIcon({ className }: { readonly className?: string }) {
  return (
    <svg aria-hidden className={className} {...SVG_PROPS}>
      <path d="M3.5 20.25h17" />
      <path d="M7 20.25v-6.5M12 20.25V7.5M17 20.25v-4" />
    </svg>
  )
}

/**
 * Manajemen Pengguna — two people, one carrying a role band.
 *
 * The short bar beside the second figure is the role chip the page's table actually renders.
 * Two figures rather than one, because this page is about a roster and never about an account.
 */
export function StaffIcon({ className }: { readonly className?: string }) {
  return (
    <svg aria-hidden className={className} {...SVG_PROPS}>
      <circle cx="9" cy="7.75" r="3.25" />
      <path d="M3.5 19.5a5.5 5.5 0 0 1 11 0" />
      <path d="M16.75 12.5h4M16.75 16h3" />
    </svg>
  )
}

/** Which mark belongs to which menu entry, keyed by `MenuEntry.id`. */
export const MENU_ICONS: Readonly<Record<string, MenuIcon>> = {
  queue: QueueIcon,
  ingest: IngestIcon,
  evaluation: EvaluationIcon,
  'admin-users': StaffIcon,
}
