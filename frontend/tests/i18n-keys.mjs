// Fails when a literal t('some.key') in the source has no translation in en, ru or uz.
// Keys built at run time (t(`a.${x}`)) are checked by pattern: the prefix must exist as a section.
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..', 'src')
const { translations } = await import(new URL('../src/i18n/translations.js', import.meta.url))

const walk = (dir) =>
  readdirSync(dir).flatMap((f) => {
    const p = join(dir, f)
    return statSync(p).isDirectory() ? walk(p) : /\.(jsx?|mjs)$/.test(f) ? [p] : []
  })

const get = (obj, path) => path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj)

let missing = 0
for (const file of walk(root)) {
  if (file.endsWith('translations.js')) continue
  const src = readFileSync(file, 'utf8')
  for (const m of src.matchAll(/\bt\(\s*(['"`])([^'"`]+)\1/g)) {
    const key = m[2]
    if (key.includes('${')) {
      // t(`section.stem_${x}`) / t(`section.${x}`): the section must exist and, for a stem, hold keys starting with it
      const head = key.split('${')[0]
      const dot = head.lastIndexOf('.')
      const section = head.slice(0, dot)
      const stem = head.slice(dot + 1)
      for (const l of ['en', 'ru', 'uz']) {
        const obj = section ? get(translations[l], section) : translations[l]
        const ok = obj && typeof obj === 'object' && (stem ? Object.keys(obj).some((k) => k.startsWith(stem)) : Object.keys(obj).length > 0)
        if (!ok) {
          console.log(`MISSING ${l}: ${head}*  (${file.replace(root, 'src')})`)
          missing++
        }
      }
      continue
    }
    for (const l of ['en', 'ru', 'uz']) {
      if (get(translations[l], key) === undefined) {
        console.log(`MISSING ${l}: ${key}  (${file.replace(root, 'src')})`)
        missing++
      }
    }
  }
}
// Dynamic keys whose finite value sets live in code: every value needs a translation.
const SETS = {
  'admin.pageSections.page': ['delivery', 'payment', 'returns', 'faq', 'contact', 'privacy', 'terms', 'manufacturing', 'quality'],
  'orderStatus.statusLabels': ['new', 'payment_pending', 'paid', 'processing', 'packed', 'shipped', 'in_transit', 'delivered', 'cancelled', 'returned', 'refunded', 'payment_failed', 'partially_refunded'],
  'orderStatus.shipmentStatus': ['shipped', 'in_transit', 'delivered', 'returned'],
}
for (const [section, values] of Object.entries(SETS)) {
  for (const l of ['en', 'ru', 'uz']) {
    for (const v of values) {
      if (get(translations[l], `${section}.${v}`) === undefined) {
        console.log(`MISSING ${l}: ${section}.${v}`)
        missing++
      }
    }
  }
}
console.log(missing ? `${missing} missing translation(s)` : 'all literal translation keys exist in en, ru and uz')
process.exit(missing ? 1 : 0)
