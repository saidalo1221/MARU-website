// Backend routes are now mounted under /api/v1 (PRD ТЗ№3 §43); kept here in
// the base URL rather than in every api/*.js call site's path string.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

const ACCESS_TOKEN_KEY = 'maru_access_token'
const CART_TOKEN_KEY = 'maru_cart_token'

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

// Guest order tokens are per-order (not global like the cart token), so
// callers pass them in explicitly rather than this module tracking one.
export async function apiRequest(
  path,
  { method = 'GET', body, orderToken, skipAuth = false, ...rest } = {}
) {
  const headers = { ...(rest.headers || {}) }
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  const accessToken = getAccessToken()
  if (accessToken && !skipAuth) headers['Authorization'] = `Bearer ${accessToken}`

  const cartToken = getCartToken()
  if (cartToken) headers['X-Cart-Token'] = cartToken

  if (orderToken) headers['X-Order-Token'] = orderToken

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
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

  return data
}
