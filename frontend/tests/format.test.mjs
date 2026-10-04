// Run with: node tests/format.test.mjs  (no test runner is installed in this project)
globalThis.localStorage = { getItem: () => 'en', setItem() {}, removeItem() {} }
const { parseApiDate, formatDate, formatDateTime } = await import('../src/lib/format.js')

const checks = [
  ['naive API timestamp is UTC', parseApiDate('2026-09-27T13:06:45').toISOString(), '2026-09-27T13:06:45.000Z'],
  ['explicit Z kept', parseApiDate('2026-09-27T13:06:45Z').toISOString(), '2026-09-27T13:06:45.000Z'],
  ['explicit offset kept', parseApiDate('2026-09-27T13:06:45+05:00').toISOString(), '2026-09-27T08:06:45.000Z'],
  ['fractional seconds', parseApiDate('2026-09-27T13:06:45.123456').toISOString(), '2026-09-27T13:06:45.123Z'],
  ['empty is blank', formatDate(null), ''],
  ['garbage is blank', formatDateTime('not a date'), ''],
  ['en date format', formatDate('2026-09-27T12:00:00', 'en-GB'), '27 Sept 2026'],
  ['ru date format', /сент/.test(formatDate('2026-09-27T12:00:00', 'ru-RU')) ? 'ok' : formatDate('2026-09-27T12:00:00', 'ru-RU'), 'ok'],
]
let bad = 0
for (const [label, got, want] of checks) {
  const ok = got === want || (label === 'en date format' && /^27 Sep(t)? 2026$/.test(got))
  if (!ok) bad += 1
  console.log(ok ? 'ok  ' : 'FAIL', label, ok ? '' : `=> ${got}`)
}
process.exit(bad ? 1 : 0)
