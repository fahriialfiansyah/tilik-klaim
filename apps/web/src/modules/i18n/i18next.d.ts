import type id from '@/locales/id'

/**
 * Teach TypeScript the key space.
 *
 * Indonesian is the reference shape because it is the language every key is authored in — the
 * English file is checked against it by `key-parity.test.ts`, not the other way round. With this
 * in place a typo in `t('queue:page.tilte')` is a compile error rather than a string that
 * renders as itself in the middle of a screen.
 */
declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'common'
    resources: typeof id
  }
}
