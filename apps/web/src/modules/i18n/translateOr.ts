import i18n from '@/modules/i18n/config'

/**
 * Translate a key that may not exist, falling back to something the reader can still act on.
 *
 * Three places need this and all three are the same situation: the server holds a vocabulary
 * this app renders — capabilities, audit event kinds, stored field names — and it can grow a
 * value we have not named yet. The reader must see *something* traceable when that happens, so
 * the fallback is the raw value rather than a blank.
 *
 * `exists` rather than comparing the result to the key, because a missing key resolves to the
 * key with its namespace **stripped**: `admin:event.X` comes back as `event.X`, an equality
 * check never fires, and `event.X` is what lands in the export instead of `X`.
 *
 * The key is a plain `string` here on purpose. Every caller builds it from a runtime value, so
 * there is no literal for the typed `t` to narrow against, and casting each call site to one
 * arbitrary sibling key would be a fiction repeated three times. The single cast below is that
 * fiction told once, in the one function whose whole job is keys that may not exist — and it is
 * the only place in the app where `t` is called untyped. `key-parity.test.ts` covers the keys
 * that *do* exist; this path is for the ones the server invents after we ship.
 */
const translateDynamic = i18n.t as unknown as (key: string) => string

export function translateOr(key: string, fallback: string): string {
  return i18n.exists(key) ? translateDynamic(key) : fallback
}
