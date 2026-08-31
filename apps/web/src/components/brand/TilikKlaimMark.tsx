/**
 * The product mark, from `design/mockup/tilik-klaim-v2.bundle.html`.
 *
 * An evidence chain closing into a loop, with the incomplete arc and the highlighted middle
 * bar drawn in amber. Colours come from `--t-inv` and `--logo-amb` rather than being fixed,
 * so the mark follows the theme instead of only working on the dark header.
 */
export function TilikKlaimMark({ className }: { readonly className?: string }) {
  return (
    <svg
      viewBox="0 0 128 128"
      className={className}
      role="img"
      aria-label="TilikKlaim"
      focusable="false"
    >
      <g fill="none" strokeLinecap="round">
        <path d="M64 12 A52 52 0 0 1 64 116" stroke="var(--t-inv)" strokeWidth="6" />
        <path
          d="M64 116 A52 52 0 0 1 12 64"
          stroke="var(--logo-amb)"
          strokeWidth="6"
          strokeDasharray="9 11"
        />
      </g>
      <circle cx="64" cy="12" r="10" fill="var(--t-inv)" />
      <circle cx="116" cy="64" r="10" fill="var(--t-inv)" />
      <circle cx="64" cy="116" r="10" fill="var(--t-inv)" />
      <circle
        cx="12"
        cy="64"
        r="9"
        fill="none"
        stroke="var(--logo-amb)"
        strokeWidth="3"
        strokeDasharray="4.71 4.71"
      />
      <rect x="47" y="46" width="34" height="8" rx="4" fill="var(--t-inv)" opacity="0.4" />
      <rect x="39" y="60" width="50" height="8" rx="4" fill="var(--logo-amb)" />
      <rect x="51" y="74" width="26" height="8" rx="4" fill="var(--t-inv)" opacity="0.4" />
    </svg>
  )
}
