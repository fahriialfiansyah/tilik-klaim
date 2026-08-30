import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layouts/AppShell'
import { AntreanReviewPage } from '@/pages/antrean/AntreanReviewPage'
import { DetailKasusPage } from '@/pages/detail-kasus/DetailKasusPage'
import { EvaluasiPage } from '@/pages/evaluasi/EvaluasiPage'
import { IngestPage } from '@/pages/ingest/IngestPage'

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<AntreanReviewPage />} />
        <Route path="cases/:id" element={<DetailKasusPage />} />
        <Route path="ingest" element={<IngestPage />} />
        <Route path="evaluation" element={<EvaluasiPage />} />
      </Route>
    </Routes>
  )
}
