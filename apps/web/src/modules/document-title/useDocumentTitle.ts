import { useEffect } from 'react'

/** The product name every tab title ends with, so a pinned tab stays identifiable at any width. */
const APP_NAME = 'TilikKlaim'

/**
 * Keep the browser tab titled after the page currently on screen.
 *
 * A route change re-renders the document body but never touches `document.title`, so a page that
 * sets no title inherits whatever the last page that did set left behind — which is how every
 * screen after sign-in came to read "Masuk · TilikKlaim". Every routed page therefore calls this,
 * and it must be called before any early return so a loading or failed state is titled too.
 *
 * The caller passes the already-translated title rather than a key: that makes a language change
 * flow through for free, because the string changes and the effect re-runs.
 */
export function useDocumentTitle(title: string): void {
  useEffect(() => {
    document.title = `${title} · ${APP_NAME}`
  }, [title])
}
