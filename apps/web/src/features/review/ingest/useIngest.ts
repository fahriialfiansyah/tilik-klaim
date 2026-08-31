import { useCallback, useEffect, useState } from 'react'

import {
  fetchSample,
  fetchSampleIndex,
  ingestBundle,
  screenBundle,
} from '@/features/review/ingest/api'
import { rejectFile } from '@/features/review/ingest/limits'
import {
  type BundleRejection,
  fromApiError,
  fromFileRejection,
  isBundleRejection,
} from '@/features/review/ingest/rejection'
import type {
  IngestBundleResponse,
  SampleSummary,
  ScreenResponse,
} from '@/features/review/ingest/types'

export type IngestStatus = 'empty' | 'submitting' | 'ready' | 'failed'
export type ScreenStatus = 'idle' | 'screening' | 'failed'

/** Where the bundle on screen came from, so the report can name it. */
export type Submission = {
  readonly label: string
  readonly detail: string
}

type IngestResult = {
  readonly samples: readonly SampleSummary[]
  readonly status: IngestStatus
  readonly submission: Submission | null
  readonly report: IngestBundleResponse | null
  /** The service did not answer. Distinct from a bundle the service refused. */
  readonly error: Error | null
  /** The bundle will not be screened, and this says which limit or rule it broke. */
  readonly rejection: BundleRejection | null
  readonly screenStatus: ScreenStatus
  readonly screenError: Error | null
  readonly submitSample: (scenario: string) => Promise<void>
  readonly submitFile: (file: File) => Promise<void>
  readonly retry: () => void
  readonly screen: () => Promise<ScreenResponse | null>
  readonly reset: () => void
}

/**
 * One bundle in, one validation report out.
 *
 * There is deliberately no configuration state here — no detector list, no threshold, no mode.
 * `sprint/00-app-spec.md` § 5 forbids a configuration wizard on this screen, and the reason is
 * not tidiness: a presenter who can tune the engine between two runs can tune their way to a
 * result, and the demo would prove nothing.
 *
 * Nothing on this screen ever hangs. Every path ends in a report, a named refusal, or an honest
 * error with a retry — `brief/01_INGEST_VALIDASI.md` § 8 singles out a spinner that never
 * resolves as the failure mode to avoid.
 */
export function useIngest(): IngestResult {
  const [samples, setSamples] = useState<readonly SampleSummary[]>([])
  const [status, setStatus] = useState<IngestStatus>('empty')
  const [submission, setSubmission] = useState<Submission | null>(null)
  const [report, setReport] = useState<IngestBundleResponse | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [rejection, setRejection] = useState<BundleRejection | null>(null)
  const [screenStatus, setScreenStatus] = useState<ScreenStatus>('idle')
  const [screenError, setScreenError] = useState<Error | null>(null)
  const [lastAttempt, setLastAttempt] = useState<(() => Promise<void>) | null>(null)

  useEffect(() => {
    let active = true
    fetchSampleIndex()
      .then((index) => active && setSamples(index))
      // The samples are a convenience; failing to list them must not take the upload zone down
      // with it, so this failure is deliberately quiet and the list simply stays empty.
      .catch(() => active && setSamples([]))
    return () => {
      active = false
    }
  }, [])

  const submit = useCallback(
    async (payload: string, next: Submission, priors: readonly string[] = []) => {
      setStatus('submitting')
      setError(null)
      setRejection(null)
      setScreenStatus('idle')
      setScreenError(null)
      setSubmission(next)

      try {
        // History first: repeat, clone, and unbundling are only visible across claims, so the
        // prior claim has to be in the store before this one is screened. Their reports are not
        // shown — the report on screen is always the bundle the operator chose.
        for (const prior of priors) {
          await ingestBundle(prior)
        }
        setReport(await ingestBundle(payload))
        setStatus('ready')
      } catch (cause: unknown) {
        setReport(null)
        if (isBundleRejection(cause)) {
          // The service answered, and its answer was "not this bundle". Reporting that as a
          // service failure would offer a retry on a file that will be refused identically
          // every time, and hide the code the operator needs to fix it.
          setRejection(fromApiError(cause))
          setStatus('ready')
          return
        }
        setError(cause instanceof Error ? cause : new Error(String(cause)))
        setStatus('failed')
      }
    },
    [],
  )

  const submitSample = useCallback(
    async (scenario: string) => {
      const attempt = async () => {
        const summary = samples.find((entry) => entry.scenario === scenario)
        const next: Submission = {
          label: summary?.label ?? scenario,
          detail: summary?.description ?? 'Kasus contoh',
        }
        setStatus('submitting')
        setSubmission(next)
        try {
          const sample = await fetchSample(scenario)
          await submit(
            JSON.stringify(sample.bundle),
            next,
            sample.history.map((prior) => JSON.stringify(prior)),
          )
        } catch (cause: unknown) {
          setReport(null)
          setError(cause instanceof Error ? cause : new Error(String(cause)))
          setStatus('failed')
        }
      }
      setLastAttempt(() => attempt)
      await attempt()
    },
    [samples, submit],
  )

  const submitFile = useCallback(
    async (file: File) => {
      const refusal = rejectFile(file)
      if (refusal) {
        // Refused here, so nothing leaves the browser. The message names the limit that was
        // broken, per `brief/01` § 8 — "too large" without the number tells an operator nothing.
        setRejection(fromFileRejection(refusal))
        setStatus('ready')
        setReport(null)
        setError(null)
        setSubmission({ label: file.name, detail: 'Berkas yang Anda unggah' })
        return
      }
      const attempt = async () => {
        const text = await file.text()
        await submit(text, {
          label: file.name,
          detail: 'Berkas yang Anda unggah',
        })
      }
      setLastAttempt(() => attempt)
      await attempt()
    },
    [submit],
  )

  const retry = useCallback(() => {
    void lastAttempt?.()
  }, [lastAttempt])

  const screen = useCallback(async (): Promise<ScreenResponse | null> => {
    if (!report?.is_screenable) {
      return null
    }
    setScreenStatus('screening')
    setScreenError(null)
    try {
      const response = await screenBundle(report.ingestion_id)
      setScreenStatus('idle')
      return response
    } catch (cause: unknown) {
      setScreenError(cause instanceof Error ? cause : new Error(String(cause)))
      setScreenStatus('failed')
      return null
    }
  }, [report])

  const reset = useCallback(() => {
    setStatus('empty')
    setSubmission(null)
    setReport(null)
    setError(null)
    setRejection(null)
    setScreenStatus('idle')
    setScreenError(null)
  }, [])

  return {
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
    reset,
  }
}
