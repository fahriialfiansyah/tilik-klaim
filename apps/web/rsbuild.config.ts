import { defineConfig } from '@rsbuild/core'
import { pluginReact } from '@rsbuild/plugin-react'

const API_ORIGIN = process.env.TILIK_API_ORIGIN ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [pluginReact()],
  html: { title: 'TilikKlaim' },
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
