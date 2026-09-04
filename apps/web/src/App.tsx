import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layouts/AppShell'
import { RequireSession } from '@/features/auth/components/RequireSession'
import { AdminUsersPage } from '@/pages/admin-users/AdminUsersPage'
import { CaseDetailPage } from '@/pages/case-detail/CaseDetailPage'
import { EvaluationPage } from '@/pages/evaluation/EvaluationPage'
import { IngestPage } from '@/pages/ingest/IngestPage'
import { LoginPage } from '@/pages/login/LoginPage'
import { QueuePage } from '@/pages/queue/QueuePage'

/**
 * `/login` sits outside `AppShell` — it has its own layout and no sidebar to render, because
 * nobody is signed in yet to decide what the sidebar would contain.
 *
 * Everything else sits behind `RequireSession`, which redirects to `/login` without a session
 * and to the role's landing page for a route that role may not reach (ADR-0006 § 2).
 */
export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireSession />}>
        <Route element={<AppShell />}>
          <Route index element={<QueuePage />} />
          <Route path="cases/:id" element={<CaseDetailPage />} />
          <Route path="ingest" element={<IngestPage />} />
          <Route path="evaluation" element={<EvaluationPage />} />
          <Route path="admin/users" element={<AdminUsersPage />} />
        </Route>
      </Route>
    </Routes>
  )
}
