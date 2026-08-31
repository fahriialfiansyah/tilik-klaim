import { useEffect, useRef } from 'react'

/**
 * Remember the last non-null value, so a closing panel can finish rendering what it was showing.
 *
 * Radix owns the mounting of a dialog's content: when `open` goes false it runs a cleanup that
 * returns focus to whatever had it before the dialog opened. Rendering the content behind a
 * second condition — `{value ? <DialogContent/> : null}` — tears that content out in the same
 * commit that flips `open`, and the focus restore never runs. The symptom is subtle and only
 * shows up on a keyboard: the drawer closes and focus lands on `<body>`, so the next Tab starts
 * again from the top of the page instead of from the control that opened the drawer.
 *
 * `brief/04_DETAIL_KASUS_DISPOSISI.md` § 9.4 makes returning focus a requirement, so keeping the
 * last value around for the closing frame is the fix rather than a workaround.
 */
export function useLastPresent<T>(value: T | null): T | null {
  const last = useRef<T | null>(value)
  useEffect(() => {
    if (value !== null) {
      last.current = value
    }
  }, [value])
  return value ?? last.current
}
