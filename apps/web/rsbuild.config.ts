import { defineConfig } from '@rsbuild/core'
import { pluginReact } from '@rsbuild/plugin-react'

export default defineConfig({
  plugins: [pluginReact()],
  html: { title: 'TilikKlaim' },
  server: { port: 3000 },
  source: { entry: { index: './src/index.tsx' } },
})
