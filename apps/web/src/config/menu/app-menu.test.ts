import { describe, expect, test } from 'vitest'

import { APP_MENU, mayReach, menuForRole } from '@/config/menu/app-menu'
import { ROLES } from '@/features/auth/types'

describe('menu is the source of truth for what each role reaches', () => {
  test('a reviewer sees the three review screens and not the admin page', () => {
    const routes = menuForRole('reviewer').map((entry) => entry.route)
    expect(routes).toEqual(['/', '/ingest', '/evaluation'])
  })

  test('a senior reviewer sees exactly what a reviewer sees', () => {
    // The two roles differ only in reopening a dismissed case, which is not a route.
    expect(menuForRole('senior_reviewer')).toEqual(menuForRole('reviewer'))
  })

  test('an administrator sees only the user-management page', () => {
    const routes = menuForRole('admin').map((entry) => entry.route)
    expect(routes).toEqual(['/admin/users'])
  })

  test('every entry declares at least one role', () => {
    for (const entry of APP_MENU) {
      expect(entry.roles.length, entry.id).toBeGreaterThan(0)
    }
  })

  test('an administrator may not reach any review route', () => {
    for (const path of ['/', '/ingest', '/evaluation', '/cases/case_1']) {
      expect(mayReach('admin', path), path).toBe(false)
    }
    expect(mayReach('admin', '/admin/users')).toBe(true)
  })

  test('a reviewer may reach case detail but not user management', () => {
    expect(mayReach('reviewer', '/cases/case_1')).toBe(true)
    expect(mayReach('reviewer', '/admin/users')).toBe(false)
  })

  test('an unknown path is refused for every role rather than defaulting to allowed', () => {
    for (const role of ROLES) {
      expect(mayReach(role, '/tidak-ada'), role).toBe(false)
    }
  })
})
