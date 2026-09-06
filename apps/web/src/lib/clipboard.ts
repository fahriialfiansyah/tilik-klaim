/**
 * Copy text, reporting honestly whether it happened.
 *
 * `navigator.clipboard` exists **only in a secure context** — HTTPS or `localhost`. This app is
 * routinely demonstrated over plain HTTP on a LAN address, where the object is not merely
 * refused but absent, and every copy button in the app silently did nothing there.
 *
 * The boolean is the contract, and it is the whole point: a caller that gets `false` must not
 * show a success state. A button that says "Tersalin" over an empty clipboard is worse than one
 * that admits it failed, because the operator walks away believing they hold the value — and
 * what they are usually copying here is the hash or version stamp they will quote in a report.
 */
export async function copyText(text: string): Promise<boolean> {
  if (text.length === 0) {
    return false
  }
  if (typeof navigator.clipboard?.writeText === 'function') {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      // Denied permission, or a context that exposes the object but not the write. The
      // selection path below still works in both cases, so this is a fall-through, not a
      // failure — the caller is told only once every route has been tried.
    }
  }
  return copyBySelection(text)
}

/**
 * The pre-`navigator.clipboard` route: put the text in an off-screen field, select it, and let
 * the document copy the selection.
 *
 * Positioned `fixed` rather than pushed off with an offset, so focusing the field cannot scroll
 * the page out from under the operator, and focus is handed back to whatever held it.
 */
function copyBySelection(text: string): boolean {
  if (typeof document.execCommand !== 'function') {
    return false
  }

  const field = document.createElement('textarea')
  field.value = text
  field.setAttribute('readonly', '')
  field.setAttribute('aria-hidden', 'true')
  field.style.cssText =
    'position:fixed;top:0;left:0;width:1px;height:1px;padding:0;border:0;opacity:0;pointer-events:none'

  const previouslyFocused = document.activeElement
  document.body.appendChild(field)

  try {
    field.select()
    field.setSelectionRange(0, text.length)
    return document.execCommand('copy')
  } catch {
    return false
  } finally {
    field.remove()
    if (previouslyFocused instanceof HTMLElement) {
      previouslyFocused.focus()
    }
  }
}
