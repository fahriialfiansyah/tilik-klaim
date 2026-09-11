import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { PageHeader, PageShell } from '@/components/layouts/PageShell'
import { Button } from '@/components/ui/button'
import {
  CompletenessBanner,
  DuplicateBanner,
  EvidenceRequestBanner,
  ServiceErrorBanner,
} from '@/features/review/ingest/components/IngestBanners'
import { IssueTable } from '@/features/review/ingest/components/IssueTable'
import { SampleList } from '@/features/review/ingest/components/SampleList'
import { UploadZone } from '@/features/review/ingest/components/UploadZone'
import { ValidationReport } from '@/features/review/ingest/components/ValidationReport'
import { useIngest } from '@/features/review/ingest/useIngest'
import { useDocumentTitle } from '@/modules/document-title/useDocumentTitle'

/** Page 3 — Ingest / Demo (`/ingest`). Widgets 1–11 per `sprint/00-app-spec.md` § 5. */
export function IngestPage() {
  const { t } = useTranslation('ingest')

  useDocumentTitle(t('page.title'))
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const fromCase = params.get('case')
  const [activeScenario, setActiveScenario] = useState<string | null>(null)

  const {
    samples,
    status,
    submission,
    report,
    error,
    rejection,
    screenStatus,
    screenError,
    submitSample,
    submitFile,
    retry,
    screen,
  } = useIngest()

  const isBusy = status === 'submitting' || screenStatus === 'screening'

  const runScreen = async () => {
    const response = await screen()
    if (response) {
      navigate(`/cases/${response.case_id}`)
    }
  }

  return (
    <PageShell>
      <PageHeader
        eyebrow={t('page.eyebrow')}
        title={t('page.title')}
        lede={t('page.lede')}
        action={
          <Button variant="outline" size="lg" onClick={() => navigate('/')}>
            {t('page.backToQueue')}
          </Button>
        }
      />

      {fromCase ? <EvidenceRequestBanner caseId={fromCase} /> : null}

      {report?.existing_case_id ? (
        <DuplicateBanner caseId={report.existing_case_id} inputHash={report.input_hash} />
      ) : null}

      {status === 'failed' ? (
        <ServiceErrorBanner
          title={t('page.checkFailed')}
          error={error}
          onRetry={retry}
        />
      ) : null}

      {screenStatus === 'failed' ? (
        <ServiceErrorBanner
          title={t('page.screenFailed')}
          error={screenError}
          onRetry={() => void runScreen()}
        />
      ) : null}

      <div className="mb-[14px] grid items-start gap-[14px] lg:grid-cols-2">
        <div className="rounded-lg border border-line bg-card p-5 shadow-panel">
          <UploadZone
            onFile={(file) => void submitFile(file)}
            rejection={rejection?.source === 'client' ? rejection.message : null}
            isBusy={isBusy}
          />
          <SampleList
            samples={samples}
            activeScenario={activeScenario}
            isBusy={isBusy}
            onPick={(scenario) => {
              setActiveScenario(scenario)
              void submitSample(scenario)
            }}
          />
        </div>

        <div>
          {submission ? (
            <p className="mb-2 text-meta text-ink-3">
              {t('page.inspected')} <strong className="text-ink">{submission.label}</strong> ·{' '}
              {submission.detail}
            </p>
          ) : null}
          <ValidationReport
            report={report}
            rejection={rejection}
            screenStatus={screenStatus}
            onScreen={() => void runScreen()}
          />
        </div>
      </div>

      {report && report.completeness_notes.length > 0 ? (
        <CompletenessBanner notes={report.completeness_notes} />
      ) : null}

      {report && report.issues.length > 0 ? <IssueTable issues={report.issues} /> : null}
      {rejection && rejection.issues.length > 0 ? (
        <IssueTable issues={rejection.issues} />
      ) : null}

      <p className="mt-4 max-w-[760px] text-small text-ink-3">{t('page.footnote')}</p>
    </PageShell>
  )
}
