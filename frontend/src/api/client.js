import { hasConsent } from '../lib/consent'
// Backend routes are now mounted under /api/v1 (PRD ТЗ№3 §43); kept here in
// the base URL rather than in every api/*.js call site's path string.
const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

const ACCESS_TOKEN_KEY = 'maru_access_token'
const CART_TOKEN_KEY = 'maru_cart_token'
const DEVICE_ID_KEY = 'maru_device_id'

// Opaque per-browser id sent with every login attempt so the backend can
// recognize a device it already challenged with an email code (see
// app/routers/auth.py's login()). Persists across logins/logouts in this
// browser — clearing site data starts a new "unrecognized device".
export function getDeviceId() {
  let id = localStorage.getItem(DEVICE_ID_KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(DEVICE_ID_KEY, id)
  }
  return id
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function setAccessToken(token) {
  if (token) localStorage.setItem(ACCESS_TOKEN_KEY, token)
  else localStorage.removeItem(ACCESS_TOKEN_KEY)
}

export function getCartToken() {
  return localStorage.getItem(CART_TOKEN_KEY)
}

export function setCartToken(token) {
  if (token) localStorage.setItem(CART_TOKEN_KEY, token)
}

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : 'Request failed')
    this.status = status
    this.detail = detail
  }
}

// FastAPI's 422 responses put `detail` as an array of {msg, loc, ...}
// objects, not a string — every call site that did `err.detail || fallback`
// would try to render that array/object directly and crash React. This
// normalizes any shape ApiError.detail can take into a displayable string.
export function errorMessage(err, fallback) {
  if (!(err instanceof ApiError)) return fallback
  // Server-side failures (5xx) and anything that is not a short plain sentence
  // (an HTML error page, a stack trace) are never shown to the visitor (PRD ТЗ№2 §55).
  if (err.status >= 500) return fallback
  const { detail } = err
  if (typeof detail === 'string' && (detail.length > 300 || /<\/?[a-z][\s\S]*>/i.test(detail))) return fallback
  // Business errors are raised as "CODE: message" (see app/core/errors.py); show only the message.
  if (typeof detail === 'string' && detail) return detail.replace(/^[A-Z][A-Z0-9_]{2,40}:\s*/, '')
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => (typeof d === 'string' ? d : d.msg)).filter(Boolean).join(', ') || fallback
  }
  return fallback
}

// Guest order tokens are per-order (not global like the cart token), so
// callers pass them in explicitly rather than this module tracking one.
export const PAGE_SIZE = 50 // the API's default page size (app/core/pagination.py)

// With `meta: true` the result is { data, total } - total is the X-Total-Count header of a paged list.
export async function apiRequest(
  path,
  { method = 'GET', body, orderToken, idempotencyKey, skipAuth = false, meta = false, ...rest } = {}
) {
  const headers = { ...(rest.headers || {}) }
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData
  // Leave Content-Type unset for FormData — the browser fills in the
  // multipart boundary itself; setting it manually breaks the upload.
  if (body !== undefined && !isFormData) headers['Content-Type'] = 'application/json'

  const accessToken = getAccessToken()
  if (accessToken && !skipAuth) headers['Authorization'] = `Bearer ${accessToken}`

  const cartToken = getCartToken()
  if (cartToken) headers['X-Cart-Token'] = cartToken

  if (orderToken) headers['X-Order-Token'] = orderToken
  // Ad platforms (GA4 / Meta) only hear about visitors who accepted analytics in the cookie banner.
  if (hasConsent('analytics')) headers['X-Analytics-Consent'] = '1'
  if (idempotencyKey) headers['Idempotency-Key'] = idempotencyKey

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? (isFormData ? body : JSON.stringify(body)) : undefined,
    ...rest,
  })

  const returnedCartToken = res.headers.get('X-Cart-Token')
  if (returnedCartToken) setCartToken(returnedCartToken)

  if (res.status === 204) return null

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!res.ok) {
    throw new ApiError(res.status, data?.detail ?? data)
  }

  if (meta) return { data, total: Number(res.headers.get('X-Total-Count') ?? (Array.isArray(data) ? data.length : 0)) }
  return data
}
