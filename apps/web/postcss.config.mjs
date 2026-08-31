/**
 * Tailwind v4 is CSS-first: the theme lives in `src/styles/app.css` under `@theme`,
 * so there is no `tailwind.config.ts`. Rsbuild picks this file up on its own.
 */
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
}
