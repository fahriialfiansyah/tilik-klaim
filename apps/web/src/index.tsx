import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import { App } from '@/App'
import { MotionProvider } from '@/components/wrappers/MotionProvider'
import { initI18n } from '@/modules/i18n'
import { initTheme } from '@/modules/theme/useTheme'
import '@/styles/app.css'

// Stamp the stored theme before the first paint so the app never flashes the wrong one.
initTheme()

// Same reason, for the same reason: resources are bundled rather than fetched, so the first
// paint is already in the right language instead of flashing the fallback and correcting itself.
initI18n()

const container = document.getElementById('root')
if (!container) {
  throw new Error('Root element #root not found. Check the Rsbuild HTML template.')
}

createRoot(container).render(
  <StrictMode>
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <MotionProvider>
        <App />
      </MotionProvider>
    </BrowserRouter>
  </StrictMode>,
)
