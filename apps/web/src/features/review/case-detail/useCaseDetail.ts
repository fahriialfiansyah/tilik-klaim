import { useCallback, useEffect, useState } from 'react'

import { fetchAudit, fetchCaseDetail, saveDisposition } from '@/features/review/case-detail/api'
import { actorLabel } from '@/features/review/case-detail/labels'
import type {
  AuditEvent,
  CaseDetail,
  DispositionRequest,
  DispositionResponse,
} from '@/features/review/case-detail/types'
import { formatDateTime } from '@/features/review/shared/format'
import i18n from '@/modules/i18n/config'
import { ApiError } from '@/lib/http'
import { useEngineVersion } from '@/modules/engine-version/useEngineVersion'

export type LoadStatus = 'loading' | 'ready' | 'failed'
export type SaveStatus = 'idle' | 'saving' | 'saved' | 'conflict' | 'failed'

/** What a stale-version rejection has to be able to tell the reviewer. */
export type VersionConflict = {
  readonly seenVersion: number
  readonly currentVersion: number
  readonly changedBy: string
  readonly changedAt: string
  readonly summary: string
}

type CaseDetailResult = {
  readonly status: LoadStatus
  readonly detail: CaseDetail | null
  readonly error: Error | null
  readonly reload: () => void
  readonly audit: readonly AuditEvent[]
  readonly auditStatus: LoadStatus
  readonly saveStatus: SaveStatus
  readonly saveError: Error | null
  readonly conflict: VersionConflict | null
  readonly save: (body: DispositionRequest) => Promise<DispositionResponse | null>
  readonly dismissConflict: () => void
}

/**
 * Server state for one case: the detail, its history, and the write path.
 *
 * Two behaviours here are requirements rather than conveniences.
 *
 * **A refused save never clears the reviewer's input.** Nothing in this hook touches the draft
 * store; a rejection only re-reads the case and reports what changed. The panel keeps every
 * word that was typed, which is the whole point of the optimistic lock being an accountability
 * guarantee rather than a concurrency nicety.
 *
 * **The screen does not move under a reader.** There is no polling, per
 * `brief/04_DETAIL_KASUS_DISPOSISI.md` § 9.2: a re-fetch happens only when the reviewer asks
 * for one, or when a save has just been refused and the fresh state is the point.
 */
export function useCaseDetail(caseId: string): CaseDetailResult {
  const setVersions = useEngineVersion((state) => state.setVersions)

  const [status, setStatus] = useState<LoadStatus>('loading')
  const [detail, setDetail] = useState<CaseDetail | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [audit, setAudit] = useState<readonly AuditEvent[]>([])
  const [auditStatus, setAuditStatus] = useState<LoadStatus>('loading')
  const [reloadToken, setReloadToken] = useState(0)

  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')
  const [saveError, setSaveError] = useState<Error | null>(null)
  const [conflict, setConflict] = useState<VersionConflict | null>(null)

  const reload = useCallback(() => setReloadToken((token) => token + 1), [])
  const dismissConflict = useCallback(() => setConflict(null), [])

  useEffect(() => {
    let active = true
    setStatus('loading')
    setError(null)

    fetchCaseDetail(caseId)
      .then((response) => {
        if (!active) {
          return
        }
        setDetail(response)
        setVersions(response.versions)
        setStatus('ready')
      })
      .catch((cause: unknown) => {
        if (!active) {
          return
        }
        setError(cause instanceof Error ? cause : new Error(String(cause)))
        setStatus('failed')
      })

    // A slow earlier response landing after a newer one would show the reviewer a different
    // case than the one they are looking at — with a disposition panel wired to it.
    return () => {
      active = false
    }
  }, [caseId, reloadToken, setVersions])

  useEffect(() => {
    let active = true
    setAuditStatus('loading')

    fetchAudit(caseId)
      .then((response) => {
        if (active) {
          setAudit(response.events)
          setAuditStatus('ready')
        }
      })
      .catch(() => {
        if (active) {
          setAudit([])
          setAuditStatus('failed')
        }
      })

    return () => {
      active = false
    }
  }, [caseId, reloadToken])

  const save = useCallback(
    async (body: DispositionRequest): Promise<DispositionResponse | null> => {
      setSaveStatus('saving')
      setSaveError(null)
      setConflict(null)

      try {
        const response = await saveDisposition(caseId, body)
        setSaveStatus('saved')
        return response
      } catch (cause: unknown) {
        const failure = cause instanceof Error ? cause : new Error(String(cause))
        setSaveError(failure)

        if (cause instanceof ApiError && cause.code === 'CASE_VERSION_CONFLICT') {
          setSaveStatus('conflict')
          setConflict(await describeConflict(caseId, body.expected_case_version))
          // Re-reading the case is what makes "muat ulang" honest: the banner offers a reload
          // and the panel behind it must already be showing the version being reloaded to.
          reload()
          return null
        }

        setSaveStatus('failed')
        return null
      }
    },
    [caseId, reload],
  )

  return {
    status,
    detail,
    error,
    reload,
    audit,
    auditStatus,
    saveStatus,
    saveError,
    conflict,
    save,
    dismissConflict,
  }
}

/**
 * Turn a 409 into the three things the reviewer actually needs: what changed, who changed it,
 * and when.
 *
 * The server's own message names the version but nothing else, and it is in English. The
 * history is where the actor and the action live, so the banner is assembled from the last
 * recorded event rather than from the error string.
 */
async function describeConflict(
  caseId: string,
  seenVersion: number,
): Promise<VersionConflict> {
  const fallback: VersionConflict = {
    seenVersion,
    currentVersion: seenVersion + 1,
    changedBy: i18n.t('review:unknown'),
    changedAt: '-',
    summary: i18n.t('caseDetail:conflict.generic'),
  }

  try {
    const [detail, history] = await Promise.all([fetchCaseDetail(caseId), fetchAudit(caseId)])
    const latest = history.events.at(-1)
    if (!latest) {
      return { ...fallback, currentVersion: detail.case_version }
    }
    return {
      seenVersion,
      currentVersion: detail.case_version,
      changedBy: actorLabel(latest.actor_role),
      changedAt: formatDateTime(latest.occurred_at),
      summary: describeEvent(latest),
    }
  } catch {
    // The conflict itself is the message that matters; failing to enrich it must not replace a
    // truthful "your save was refused" with a second, unrelated error.
    return fallback
  }
}

/**
 * The sentence a version conflict is explained with.
 *
 * Not a component, so it reads the running i18next instance rather than a hook — the conflict is
 * raised from a save handler, and the reviewer reads the answer in whichever language the screen
 * they were looking at is in.
 */
function describeEvent(event: AuditEvent): string {
  const after = event.state_after
    ? i18n.t(`caseDetail:state.${event.state_after}` as 'caseDetail:page.breadcrumb')
    : null
  if (event.structured_reason && after) {
    return i18n.t('caseDetail:conflict.withReason', {
      state: after,
      reason: event.structured_reason,
    })
  }
  if (after) {
    return i18n.t('caseDetail:conflict.stateOnly', { state: after })
  }
  return i18n.t('caseDetail:conflict.generic')
}
