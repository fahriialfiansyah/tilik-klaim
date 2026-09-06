/**
 * How much of the input hash is shown.
 *
 * Twelve characters identify a submission among anything an operator holds at once, and the
 * whole 64 wrapped onto a second line and dominated whatever it sat in. The full value stays
 * reachable — on the element's `title`, and on the clipboard — but it is never what is read.
 */
const HASH_PREFIX_LENGTH = 12

/**
 * The hash as it appears on screen, everywhere it appears.
 *
 * Shared rather than repeated, because the duplicate banner and the validation report describe
 * the *same* submission: a bundle that reads as `sha256:c0e8fde4f74a…` in one place and as
 * something else in the other is two bundles as far as the reader is concerned.
 */
export function shortHash(inputHash: string): string {
  return `sha256:${inputHash.slice(0, HASH_PREFIX_LENGTH)}…`
}
