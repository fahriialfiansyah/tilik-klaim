import type { CSSProperties } from 'react'

/**
 * The product mark, from `design/mockup/tilik-klaim-v2.bundle.html`.
 *
 * An evidence chain closing into a loop, with the incomplete arc and the highlighted middle
 * bar drawn in amber. Colours come from `--t-inv` and `--logo-amb` rather than being fixed,
 * so the mark follows the theme instead of only working on the dark header.
 *
 * `drawn` exists for the login page, where the mark strokes itself in once on load: the solid
 * arc draws, then the incomplete amber arc and the nodes arrive behind it. It defaults to
 * `true`, so every other caller gets the finished mark with no animation and no extra prop.
 *
 * The amber arc is **not** drawn with `stroke-dashoffset` — its dash pattern is part of the
 * design, and animating the offset of a dashed stroke slides the dashes along instead of
 * revealing them. It fades in behind the solid arc instead, which is the honest way to animate
 * a shape whose dashes carry meaning.
 *
 * `onSurface` swaps the solid stroke from `--t-inv` to `currentColor`. The default is built for
 * the dark header, where inverse ink is correct; on a card or page surface that same value is
 * near-white and the mark disappears. The amber stays amber in both — it is the one part of the
 * mark that carries meaning rather than contrast.
 */
export function TilikKlaimMark({
  className,
  drawn = true,
  drawMs = 700,
  onSurface = false,
}: {
  readonly className?: string
  readonly drawn?: boolean
  readonly drawMs?: number
  /** Draw on a light card or page surface instead of the dark header. */
  readonly onSurface?: boolean
}) {
  const ink = onSurface ? 'currentColor' : 'var(--t-inv)'
  const trunk: CSSProperties = {
    strokeDasharray: 100,
    strokeDashoffset: drawn ? 0 : 100,
    transition: `stroke-dashoffset ${drawMs}ms ease-out`,
  }
  const settle = (delayFraction: number): CSSProperties => ({
    opacity: drawn ? 1 : 0,
    transition: `opacity 260ms ease-out ${Math.round(drawMs * delayFraction)}ms`,
  })

  return (
    <svg
      viewBox="0 0 128 128"
      className={className}
      role="img"
      aria-label="TilikKlaim"
      focusable="false"
    >
      <g fill="none" strokeLinecap="round">
        <path
          d="M64 12 A52 52 0 0 1 64 116"
          stroke={ink}
          strokeWidth="6"
          pathLength={100}
          style={trunk}
        />
        <path
          d="M64 116 A52 52 0 0 1 12 64"
          stroke="var(--logo-amb)"
          strokeWidth="6"
          strokeDasharray="9 11"
          style={settle(0.7)}
        />
      </g>
      <g style={settle(0.55)}>
        <circle cx="64" cy="12" r="10" fill={ink} />
        <circle cx="116" cy="64" r="10" fill={ink} />
        <circle cx="64" cy="116" r="10" fill={ink} />
        <circle
          cx="12"
          cy="64"
          r="9"
          fill="none"
          stroke="var(--logo-amb)"
          strokeWidth="3"
          strokeDasharray="4.71 4.71"
        />
      </g>
      <g style={settle(0.85)}>
        <rect x="47" y="46" width="34" height="8" rx="4" fill={ink} opacity="0.4" />
        <rect x="39" y="60" width="50" height="8" rx="4" fill="var(--logo-amb)" />
        <rect x="51" y="74" width="26" height="8" rx="4" fill={ink} opacity="0.4" />
      </g>
    </svg>
  )
}
