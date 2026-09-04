import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu'
import type { ComponentProps } from 'react'

import { cn } from '@/lib/utils'

/**
 * shadcn DropdownMenu, bound to the TilikKlaim tokens.
 *
 * Radix owns the behaviour and that is the reason to use it: focus management, Escape,
 * click-outside, arrow-key roving, the portal, and `aria-expanded` are all its, tested far more
 * thoroughly than this project could test its own.
 *
 * **Unlike `dialog.tsx`, focus return needs nothing added here.** That file restores focus by
 * hand because every drawer in the app is opened from an ordinary button rather than a
 * `DialogTrigger`, so Radix's own restore aims at a null ref. A dropdown *always* has a
 * `DropdownMenuTrigger` — it is not optional in the primitive — so Radix returns focus to it on
 * close without help. Copying the dialog's manual restore here would fight a mechanism that
 * already works.
 */
export const DropdownMenu = DropdownMenuPrimitive.Root
export const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger

export function DropdownMenuContent({
  className,
  sideOffset = 6,
  align = 'end',
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.Content>) {
  return (
    <DropdownMenuPrimitive.Portal>
      <DropdownMenuPrimitive.Content
        sideOffset={sideOffset}
        align={align}
        className={cn(
          'z-50 min-w-[260px] overflow-hidden rounded-lg border border-line bg-card p-1 text-ink shadow-panel',
          className,
        )}
        {...props}
      />
    </DropdownMenuPrimitive.Portal>
  )
}

export function DropdownMenuItem({
  className,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.Item>) {
  return (
    <DropdownMenuPrimitive.Item
      className={cn(
        'flex w-full cursor-pointer items-center gap-2 rounded-md px-[10px] py-[7px] text-body outline-none data-[highlighted]:bg-accent data-[highlighted]:text-brand',
        className,
      )}
      {...props}
    />
  )
}

export function DropdownMenuSeparator({
  className,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.Separator>) {
  return (
    <DropdownMenuPrimitive.Separator
      className={cn('my-1 h-px bg-line', className)}
      {...props}
    />
  )
}

export function DropdownMenuLabel({
  className,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.Label>) {
  return (
    <DropdownMenuPrimitive.Label className={cn('px-[10px] py-2', className)} {...props} />
  )
}
