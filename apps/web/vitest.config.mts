import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  test: {
    environment: 'jsdom',
    // Deliberately NOT Asia/Jakarta.
    //
    // Every timestamp this app prints is pinned to `Asia/Jakarta` by `src/lib/datetime.ts`, and
    // a suite running in that same zone cannot tell a pinned formatter from one that merely
    // inherited the developer's laptop. Running the tests somewhere else — and on the other side
    // of the date line from WIB, so a wrong zone shifts the calendar day and not only the hour —
    // makes the pin a property the suite enforces rather than a comment it trusts.
    env: { TZ: 'America/New_York' },
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.test.{ts,tsx}', 'src/test/**', 'src/index.tsx'],
    },
  },
})
