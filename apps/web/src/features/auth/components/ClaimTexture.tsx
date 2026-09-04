/**
 * The page's background, generated from the shape of the data the product works on.
 *
 * Rows of billed claim lines with their evidence connectors, and — sparsely — an amber segment
 * where a line has no support. That is the whole product in one texture, and it costs nothing
 * to license: this file draws it, so the submission checklist's "visual licenses documented"
 * line is answered by a sentence rather than by a search.
 *
 * **It is not a photograph and carries no organisation's marks.** `design/DESIGN.md` puts trust
 * in hierarchy and provenance rather than decoration, and the competition's originality rule
 * forbids using intellectual property that is not ours — the organiser's included.
 *
 * Kept at a low opacity on purpose: above roughly 6% it starts competing with the matrix, and
 * the matrix is the point of this screen. Decorative, so it is hidden from assistive technology.
 */
export function ClaimTexture({ className }: { readonly className?: string }) {
  return (
    <svg
      aria-hidden
      className={className}
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid slice"
      viewBox="0 0 1440 900"
    >
      <defs>
        {/* One tile = two claim lines hanging off a shared evidence connector. */}
        <pattern id="tk-claim-rows" width="248" height="72" patternUnits="userSpaceOnUse">
          <rect x="10" y="12" width="2" height="52" fill="currentColor" opacity="0.16" />
          <circle cx="11" cy="17" r="3.5" fill="currentColor" opacity="0.2" />
          <circle cx="11" cy="53" r="3.5" fill="currentColor" opacity="0.2" />
          <rect x="26" y="14" width="112" height="6" rx="3" fill="currentColor" opacity="0.14" />
          <rect x="148" y="14" width="52" height="6" rx="3" fill="currentColor" opacity="0.09" />
          <rect x="26" y="50" width="74" height="6" rx="3" fill="currentColor" opacity="0.14" />
          <rect x="110" y="50" width="104" height="6" rx="3" fill="currentColor" opacity="0.09" />
        </pattern>
        {/* A much larger tile, so the gaps stay rare — they mean something. */}
        <pattern id="tk-claim-gaps" width="744" height="360" patternUnits="userSpaceOnUse">
          <rect x="174" y="86" width="96" height="6" rx="3" fill="var(--logo-amb)" opacity="0.22" />
          <rect x="522" y="230" width="72" height="6" rx="3" fill="var(--logo-amb)" opacity="0.18" />
          <rect x="66" y="302" width="58" height="6" rx="3" fill="var(--logo-amb)" opacity="0.15" />
        </pattern>
      </defs>
      <rect width="1440" height="900" fill="url(#tk-claim-rows)" />
      <rect width="1440" height="900" fill="url(#tk-claim-gaps)" />
    </svg>
  )
}
