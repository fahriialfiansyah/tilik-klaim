import { Slot } from '@radix-ui/react-slot'
import { type VariantProps, cva } from 'class-variance-authority'
import { forwardRef, type ComponentProps } from 'react'

import { cn } from '@/lib/utils'

/**
 * shadcn Button, bound to the TilikKlaim tokens.
 *
 * shadcn's `destructive` variant is deliberately **absent**. `design/DESIGN.md` reserves red
 * for deterministic conflict — it marks a certain conflict, never a culpable party — and this
 * app has no destructive action for it to mean. Leaving the variant in would make misuse a
 * one-word edit away.
 */
const buttonVariants = cva(
  'inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium outline-none transition-colors disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*=size-])]:size-4',
  {
    variants: {
      variant: {
        primary: 'bg-brand text-brand-on hover:bg-brand-hover',
        outline: 'border border-line bg-card text-ink hover:border-brand hover:text-brand',
        subtle: 'bg-sunk text-ink hover:bg-accent',
        ghost: 'text-ink hover:bg-accent',
        link: 'text-brand underline underline-offset-4 hover:text-brand-hover',
      },
      size: {
        sm: 'h-8 px-3 text-small',
        md: 'h-9 px-4 text-body',
        lg: 'h-11 px-[18px] text-body-lg',
        icon: 'size-8',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

type ButtonProps = ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    /** Render the child element instead of a `button`, keeping the styling. */
    readonly asChild?: boolean
  }

/**
 * `forwardRef` because this app is on React 18, where `ref` is not an ordinary prop.
 *
 * The login form needs it: `Pakai` fills both fields and then moves focus to submit, so a
 * reviewer switching persona mid-demo presses one button and Enter. Without a forwarded ref the
 * focus call would silently do nothing — the kind of defect only a keyboard finds.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant, size, asChild = false, ...props },
  ref,
) {
  const Component = asChild ? Slot : 'button'
  return (
    <Component
      ref={ref}
      data-slot="button"
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  )
})

export { buttonVariants }
