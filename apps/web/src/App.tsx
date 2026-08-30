import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layouts/AppShell'
import { CaseDetailPage } from '@/pages/case-detail/CaseDetailPage'
import { EvaluationPage } from '@/pages/evaluation/EvaluationPage'
import { IngestPage } from '@/pages/ingest/IngestPage'
import { QueuePage } from '@/pages/queue/QueuePage'

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<QueuePage />} />
        <Route path="cases/:id" element={<CaseDetailPage />} />
        <Route path="ingest" element={<IngestPage />} />
        <Route path="evaluation" element={<EvaluationPage />} />
      </Route>
    </Routes>
  )
}
