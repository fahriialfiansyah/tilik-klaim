import { renderHook, waitFor } from '@testing-library/react'
import { act } from 'react'
import { beforeEach, describe, expect, test, vi } from 'vitest'

import { fetchUserAudit, fetchUsers, updateUser } from '@/features/admin/users/api'
import type { UserAuditEvent } from '@/features/admin/users/types'
import { useUsers } from '@/features/admin/users/useUsers'
import type { StaffUser } from '@/features/auth/types'
import { ApiError } from '@/lib/http'

vi.mock('@/features/admin/users/api')

const SARI: StaffUser = {
  user_id: 'usr_sari_wulandari',
  staff_code: 'PTG-01',
  full_name: 'Sari Wulandari',
  email: 'sari.wulandari@rsud-demo.example',
  role: 'reviewer',
  is_active: true,
  last_signed_in_at: '2026-09-04T02:15:00Z',
}

const PROMOTION: UserAuditEvent = {
  event_id: 'uevt_promote',
  event_kind: 'USER_ROLE_CHANGED',
  actor_user_id: 'usr_rina_hartati',
  actor_role: 'admin',
  target_user_id: SARI.user_id,
  field: 'role',
  value_before: 'reviewer',
  value_after: 'senior_reviewer',
  occurred_at: '2026-09-05T10:00:00Z',
}

const DEACTIVATION: UserAuditEvent = {
  ...PROMOTION,
  event_id: 'uevt_off',
  event_kind: 'USER_DEACTIVATED',
  field: 'is_active',
  value_before: 'true',
  value_after: 'false',
}

beforeEach(() => {
  vi.mocked(fetchUsers).mockResolvedValue({ users: [SARI] })
  vi.mocked(fetchUserAudit).mockResolvedValue({ events: [] })
  vi.mocked(updateUser).mockReset()
})

async function loaded() {
  const view = renderHook(() => useUsers())
  await waitFor(() => expect(view.result.current.status).toBe('ready'))
  return view
}

describe('undoing a change', () => {
  test('offers the previous value the server recorded, not the row we happened to hold', () => {
    // `value_before` is what was actually written. A client-side "what it used to be" can
    // disagree with it after a second administrator changes the same row.
    expect(PROMOTION.value_before).toBe('reviewer')
  })

  test('proposes a patch back to the role the event recorded', async () => {
    vi.mocked(updateUser).mockResolvedValue({
      user: { ...SARI, role: 'senior_reviewer' },
      events: [PROMOTION],
    })
    const { result } = await loaded()

    await act(() => result.current.change(SARI.user_id, { role: 'senior_reviewer' }))

    expect(result.current.undoable?.patch).toEqual({ role: 'reviewer' })
    expect(result.current.undoable?.summary).toContain('Sari Wulandari')
  })

  test('appends a reversing change and leaves the original event in the trail', async () => {
    vi.mocked(updateUser).mockResolvedValueOnce({
      user: { ...SARI, role: 'senior_reviewer' },
      events: [PROMOTION],
    })
    const { result } = await loaded()
    await act(() => result.current.change(SARI.user_id, { role: 'senior_reviewer' }))

    const reversal: UserAuditEvent = {
      ...PROMOTION,
      event_id: 'uevt_undo',
      value_before: 'senior_reviewer',
      value_after: 'reviewer',
    }
    vi.mocked(updateUser).mockResolvedValueOnce({ user: SARI, events: [reversal] })

    await act(() => result.current.undo())

    // The point of the whole feature: two events, not one edited one. Undo is a new record of a
    // move back, exactly as ADR-0001 treats a corrected disposition.
    expect(result.current.events.map((event) => event.event_id)).toEqual([
      'uevt_undo',
      'uevt_promote',
    ])
    expect(vi.mocked(updateUser).mock.calls[1]).toEqual([SARI.user_id, { role: 'reviewer' }])
  })

  test('an undo offers no undo of its own', async () => {
    vi.mocked(updateUser).mockResolvedValue({
      user: { ...SARI, is_active: false },
      events: [DEACTIVATION],
    })
    const { result } = await loaded()
    await act(() => result.current.change(SARI.user_id, { is_active: false }))
    expect(result.current.undoable).not.toBeNull()

    await act(() => result.current.undo())

    // Two buttons that flip each other forever is a control nobody can tell the state of.
    expect(result.current.undoable).toBeNull()
  })

  test('reactivating proposes deactivating again, read off the flag that was stored', async () => {
    vi.mocked(updateUser).mockResolvedValue({
      user: { ...SARI, is_active: false },
      events: [DEACTIVATION],
    })
    const { result } = await loaded()

    await act(() => result.current.change(SARI.user_id, { is_active: false }))

    expect(result.current.undoable?.patch).toEqual({ is_active: true })
  })

  test('a refused change offers nothing to undo and keeps the roster on screen', async () => {
    vi.mocked(updateUser).mockRejectedValue(
      new ApiError(409, {
        code: 'USER_SELF_MODIFICATION_REFUSED',
        detail: 'Anda tidak dapat menonaktifkan akun Anda sendiri.',
      }),
    )
    const { result } = await loaded()

    await act(() => result.current.change(SARI.user_id, { is_active: false }))

    // A refusal answers one action; it is not an outage, and the table keeps its data.
    expect(result.current.status).toBe('ready')
    expect(result.current.users).toEqual([SARI])
    expect(result.current.undoable).toBeNull()
    expect(result.current.refusal?.code).toBe('USER_SELF_MODIFICATION_REFUSED')
  })
})
