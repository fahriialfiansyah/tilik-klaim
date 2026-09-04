import { defineConfig } from '@rsbuild/core'
import { pluginReact } from '@rsbuild/plugin-react'

const API_ORIGIN = process.env.TILIK_API_ORIGIN ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [pluginReact()],
  html: {
    title: 'TilikKlaim',
    /**
     * The mark on the header's navy, as an SVG so it stays sharp at every tab size. Its colours
     * are literal rather than tokenised — browser chrome renders a favicon with no access to the
     * page's custom properties, so `TilikKlaimMark.tsx`'s theme-following version cannot be
     * reused here. See the comment at the top of the file.
     */
    favicon: './src/assets/favicon.svg',
  },
  server: {
    port: 3000,
    /**
     * The API is proxied rather than called cross-origin, so the browser stays same-origin and
     * the backend needs no CORS middleware. Widening CORS for a dev convenience would add a
     * security surface that production — where both sit behind one origin — does not need.
     */
    proxy: {
      '/v1': { target: API_ORIGIN, changeOrigin: true },
    },
  },
  source: { entry: { index: './src/index.tsx' } },
})
