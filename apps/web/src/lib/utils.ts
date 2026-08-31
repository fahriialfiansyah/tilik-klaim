import { type ClassValue, clsx } from 'clsx'
import { extendTailwindMerge } from 'tailwind-merge'

/**
 * `tailwind-merge` has to be told about this project's type scale.
 *
 * The `text-*` utility serves two theme namespaces at once — font size (`--text-*`) and colour
 * (`--color-*`). tailwind-merge only knows Tailwind's stock scale, so it read `text-body-lg` as
 * a *colour*, decided it conflicted with `text-brand-on`, and kept only the last one. Every
 * Button lost its text colour that way: `bg-brand text-brand-on` plus a size variant merged down
 * to `bg-brand text-body-lg`, leaving near-black body text on dark teal at 2.5:1.
 *
 * Naming the sizes here puts them in the font-size group, so colours stop colliding with them.
 * Anything added to the `--text-*` block in `app.css` must be added here too.
 */
const FONT_SIZES = ['micro', 'meta', 'small', 'body', 'body-lg', 'lead', 'title', 'page']

const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      'font-size': [{ text: FONT_SIZES }],
    },
  },
})

/** Merge conditional class names, letting later Tailwind utilities win. Used by shadcn components. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
