import { describe, expect, test } from 'vitest'

import en from '@/locales/en'
import id from '@/locales/id'
import { LOCALES } from '@/modules/i18n/locales'

/**
 * The two locale trees must hold exactly the same keys.
 *
 * This is the test that makes a second language safe to ship. A key present in Indonesian and
 * missing from English does not fail a build, does not throw, and does not render blank — it
 * renders **the key itself**, so a screen quietly shows `page.lede` where a paragraph belongs,
 * and only a person reading that screen in that language would ever notice.
 *
 * It has already earned its place once. A batch edit replaced the whole of `admin.undo` instead
 * of merging into it, taking four keys with it; nothing else in the suite noticed, and the
 * screens that used them would have rendered raw key strings.
 *
 * Placeholders are checked too, for the same reason with a sharper edge: `{{name}}` dropped
 * from one language does not break the sentence, it silently removes the fact the sentence was
 * written to carry.
 */

type Tree = { readonly [key: string]: string | readonly string[] | Tree }

function flatten(tree: Tree, prefix = ''): Map<string, string> {
  const out = new Map<string, string>()
  for (const [key, value] of Object.entries(tree)) {
    const path = prefix ? `${prefix}.${key}` : key
    if (Array.isArray(value)) {
      // Reason lists are ordered options a reviewer picks from; the *count* has to match, since
      // an option missing in one language is a choice that language cannot make.
      value.forEach((entry, index) => out.set(`${path}[${index}]`, entry))
    } else if (typeof value === 'object' && value !== null) {
      for (const [nested, text] of flatten(value as Tree, path)) {
        out.set(nested, text)
      }
    } else {
      out.set(path, value as string)
    }
  }
  return out
}

const PLACEHOLDER = /\{\{(\w+)\}\}/g

function placeholders(text: string): readonly string[] {
  return [...text.matchAll(PLACEHOLDER)].map((match) => match[1]).sort()
}

const trees = { id: flatten(id as unknown as Tree), en: flatten(en as unknown as Tree) }

describe('the locale files stay in step', () => {
  test('every namespace exists in both languages', () => {
    expect(Object.keys(id).sort()).toEqual(Object.keys(en).sort())
  })

  test('English holds every key Indonesian does', () => {
    const missing = [...trees.id.keys()].filter((key) => !trees.en.has(key))
    expect(missing, 'keys missing from en').toEqual([])
  })

  test('Indonesian holds every key English does', () => {
    // The other direction matters just as much: a key only English has is dead weight nobody
    // reads, and usually the sign of a rename applied to one file and not the other.
    const missing = [...trees.en.keys()].filter((key) => !trees.id.has(key))
    expect(missing, 'keys missing from id').toEqual([])
  })

  test('a sentence needing a fact needs it in both languages', () => {
    const mismatched = [...trees.id.entries()]
      .filter(([key, text]) => {
        const other = trees.en.get(key)
        return other !== undefined && placeholders(text).join() !== placeholders(other).join()
      })
      .map(([key]) => key)
    expect(mismatched, 'placeholders differ between languages').toEqual([])
  })

  test('no value is blank in either language', () => {
    for (const [locale, tree] of Object.entries(trees)) {
      const blank = [...tree.entries()].filter(([, text]) => text.trim() === '')
      expect(blank.map(([key]) => key), `blank values in ${locale}`).toEqual([])
    }
  })

  test('the locale list and the resource files agree', () => {
    expect([...LOCALES].sort()).toEqual(['en', 'id'])
  })
})
