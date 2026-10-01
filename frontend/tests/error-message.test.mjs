// Run with: node tests/error-message.test.mjs  (no test runner is installed in this project)
// errorMessage must never show server errors or HTML to the visitor (PRD ТЗ№2 §55).
globalThis.localStorage = { getItem: () => null, setItem() {}, removeItem() {} }
const { ApiError, errorMessage } = await import('../src/api/client.js')

const FALLBACK = 'Something went wrong. Please try again.'
const checks = [
  ['400 keeps a short plain sentence', errorMessage(new ApiError(400, 'Email already registered'), FALLBACK), 'Email already registered'],
  ['coded business error shows only the message', errorMessage(new ApiError(400, 'INSUFFICIENT_STOCK: not enough stock for SKU X'), FALLBACK), 'not enough stock for SKU X'],
  ['500 is hidden', errorMessage(new ApiError(500, 'Failed to fetch products'), FALLBACK), FALLBACK],
  ['502 is hidden', errorMessage(new ApiError(502, 'Bad gateway'), FALLBACK), FALLBACK],
  ['HTML body is hidden', errorMessage(new ApiError(404, '<html><body>Not Found</body></html>'), FALLBACK), FALLBACK],
  ['422 list is joined', errorMessage(new ApiError(422, [{ msg: 'field required' }, { msg: 'too short' }]), FALLBACK), 'field required, too short'],
  ['network error uses fallback', errorMessage(new TypeError('Failed to fetch'), FALLBACK), FALLBACK],
  ['very long text is hidden', errorMessage(new ApiError(400, 'x'.repeat(400)), FALLBACK), FALLBACK],
]
let bad = 0
for (const [label, got, want] of checks) {
  const ok = got === want
  if (!ok) bad += 1
  console.log(ok ? 'ok  ' : 'FAIL', label, ok ? '' : `=> ${got}`)
}
process.exit(bad ? 1 : 0)
