import * as DialogPrimitive from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import {
  createContext,
  forwardRef,
  useContext,
  useRef,
  type ComponentProps,
  type ReactNode,
} from 'react'

import { cn } from '@/lib/utils'

/**
 * shadcn Dialog, bound to the TilikKlaim tokens, in two shapes: a centred modal and a
 * right-hand drawer.
 *
 * Radix owns the behaviour and that is why it is here rather than a hand-rolled overlay.
 * `sprint/00-app-spec.md` § 4 rule 5 requires the whole flow — opening and closing the
 * comparison drawer included — to work from the keyboard. Focus trapping, Escape, the portal,
 * `aria-modal`, and scroll locking are all Radix's, tested far more thoroughly than this project
 * could test its own.
 *
 * The one behaviour added on top is returning focus on close; see `Dialog` below for why
 * Radix's own restore cannot fire in this app.
 */

export const DialogTrigger = DialogPrimitive.Trigger
export const DialogClose = DialogPrimitive.Close

type FocusTarget = { current: HTMLElement | null }
const ReturnFocusContext = createContext<FocusTarget | null>(null)

/**
 * Radix's `Root`, plus the one thing it cannot do on its own here: return focus.
 *
 * On close Radix calls `event.preventDefault()` and focuses `DialogTrigger`'s ref. Every drawer
 * on the case-detail screen is opened from an ordinary button — the trigger is whichever of two
 * dozen evidence references was clicked, not one declared element — so that ref is null, the
 * default restore is suppressed, and focus lands on `<body>`. A keyboard reviewer closing the
 * source panel would find their next Tab starting again from the page header.
 *
 * `brief/04_DETAIL_KASUS_DISPOSISI.md` § 9.4 requires focus to come back somewhere sensible, so
 * the element that had it is captured here on the way open and restored on the way closed.
 */
export function Dialog({
  open,
  children,
  ...props
}: ComponentProps<typeof DialogPrimitive.Root>) {
  const returnFocus = useRef<HTMLElement | null>(null)
  const wasOpen = useRef(false)

  // Captured during render, not in an effect: React runs a parent's effects *after* its
  // children's, and by then Radix's focus scope has already moved focus into the dialog.
  if (open && !wasOpen.current && typeof document !== 'undefined') {
    returnFocus.current = document.activeElement as HTMLElement | null
  }
  wasOpen.current = Boolean(open)

  return (
    <ReturnFocusContext.Provider value={returnFocus}>
      <DialogPrimitive.Root open={open} {...props}>
        {children}
      </DialogPrimitive.Root>
    </ReturnFocusContext.Provider>
  )
}

/**
 * `forwardRef`, because Radix gives this one a ref and React 18 has no other way to accept it.
 *
 * `Presence` clones the overlay to drive its mount/unmount, and a plain function component in
 * between swallowed the ref — logging "Function components cannot be given refs" on every dialog
 * this app opens, and leaving Radix without the node it measures.
 */
const DialogOverlay = forwardRef<
  HTMLDivElement,
  ComponentProps<typeof DialogPrimitive.Overlay>
>(function DialogOverlay({ className, ...props }, ref) {
  return (
    <DialogPrimitive.Overlay
      ref={ref}
      className={cn('fixed inset-0 z-40 bg-[rgba(9,20,26,0.45)]', className)}
      {...props}
    />
  )
})

type DialogContentProps = ComponentProps<typeof DialogPrimitive.Content> & {
  /** `modal` centres; `drawer` slides in from the right and fills the height. */
  readonly variant?: 'modal' | 'drawer'
  readonly title: string
  readonly description?: ReactNode
  readonly closeLabel?: string
}

const VARIANT_CLASSES = {
  modal:
    'fixed top-1/2 left-1/2 z-50 w-[min(560px,calc(100vw-32px))] -translate-x-1/2 -translate-y-1/2 rounded-lg border border-line bg-card shadow-panel',
  drawer:
    'fixed top-0 right-0 z-50 flex h-full w-[min(720px,calc(100vw-48px))] flex-col border-l border-line bg-card shadow-panel',
} as const

export function DialogContent({
  variant = 'modal',
  title,
  description,
  closeLabel = 'Tutup',
  className,
  children,
  ...props
}: DialogContentProps) {
  const returnFocus = useContext(ReturnFocusContext)

  return (
    <DialogPrimitive.Portal>
      <DialogOverlay />
      <DialogPrimitive.Content
        className={cn(VARIANT_CLASSES[variant], className)}
        onCloseAutoFocus={(event) => {
          // Pre-empts Radix's own handler, which would aim at a `DialogTrigger` this app does
          // not use. Preventing the default keeps the browser from scrolling to the restored
          // element as well, which on this page would jump the reader away from what they read.
          event.preventDefault()
          returnFocus?.current?.focus({ preventScroll: true })
        }}
        {...props}
      >
        <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div className="min-w-0">
            <DialogPrimitive.Title className="text-lead font-semibold text-pretty">
              {title}
            </DialogPrimitive.Title>
            {description ? (
              <DialogPrimitive.Description asChild>
                <div className="mt-[6px] text-small text-ink-2 text-pretty">{description}</div>
              </DialogPrimitive.Description>
            ) : null}
          </div>
          <DialogPrimitive.Close
            aria-label={closeLabel}
            className="shrink-0 rounded-md border border-line bg-card p-[6px] text-ink-2 hover:border-brand hover:text-brand"
          >
            <X className="size-4" />
          </DialogPrimitive.Close>
        </div>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  )
}
