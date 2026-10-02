import { useCallback, useRef, useState } from 'react'

import type { Citation } from '@/features/review/assistant/types'
import { fetchCaseDetail } from '@/features/review/case-detail/api'
import type { CaseDetail, EvidenceRef } from '@/features/review/case-detail/types'

export type SourceDrawerState = {
  readonly reference: EvidenceRef | null
  readonly detail: CaseDetail | null
  readonly isOpening: boolean
  readonly hasFailed: boolean
}

const FAILURE_NOTICE_MS = 5000

const CLOSED: SourceDrawerState = { reference: null, detail: null, isOpening: false, hasFailed: false }

/**
 * Open a cited resource in the same drawer the case detail uses.
 *
 * The drawer needs the case's source index to say which of the four availabilities applies, so
 * the case is fetched — once, then kept for this page's lifetime — the first time one of its
 * resources is opened. A citation is a reference that opens, and this is where it opens.
 */
export function useSourceDrawer(): {
  readonly state: SourceDrawerState
  readonly open: (citation: Citation) => void
  readonly close: () => void
} {
  const [state, setState] = useState<SourceDrawerState>(CLOSED)
  const cache = useRef(new Map<string, CaseDetail>())
  // Each open gets a number; a fetch that resolves after a newer open — or after close — is
  // dropped, so the drawer never shows the resource the reviewer moved away from.
  const latest = useRef(0)
  const failureTimer = useRef<number | undefined>(undefined)

  const open = useCallback((citation: Citation) => {
    if (
      citation.kind !== 'RESOURCE' ||
      !citation.case_id ||
      !citation.resource_type ||
      !citation.resource_id
    ) {
      return
    }
    const reference: EvidenceRef = {
      resource_type: citation.resource_type,
      resource_id: citation.resource_id,
      label: citation.label,
    }
    const caseId = citation.case_id
    const request = ++latest.current
    window.clearTimeout(failureTimer.current)
    const cached = cache.current.get(caseId)
    if (cached) {
      setState({ reference, detail: cached, isOpening: false, hasFailed: false })
      return
    }
    setState({ ...CLOSED, isOpening: true })
    fetchCaseDetail(caseId)
      .then((detail) => {
        cache.current.set(caseId, detail)
        if (request === latest.current) {
          setState({ reference, detail, isOpening: false, hasFailed: false })
        }
      })
      .catch(() => {
        if (request !== latest.current) {
          return
        }
        setState({ ...CLOSED, hasFailed: true })
        // The notice says what happened and then gets out of the way.
        failureTimer.current = window.setTimeout(() => setState(CLOSED), FAILURE_NOTICE_MS)
      })
  }, [])

  const close = useCallback(() => {
    latest.current += 1
    setState(CLOSED)
  }, [])
  return { state, open, close }
}
