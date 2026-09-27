import { apiRequest, setAccessToken } from './client'

export async function register(payload) {
  const token = await apiRequest('/auth/register', { method: 'POST', body: payload })
  setAccessToken(token.access_token)
  return token
}

export async function login(email, password) {
  const token = await apiRequest('/auth/login', { method: 'POST', body: { email, password } })
  setAccessToken(token.access_token)
  return token
}

export function logout() {
  setAccessToken(null)
}

export function requestAdminCode(email, password) {
  return apiRequest('/auth/admin/login', { method: 'POST', body: { email, password } })
}

export async function verifyAdminCode(email, code) {
  const token = await apiRequest('/auth/admin/verify', { method: 'POST', body: { email, code } })
  setAccessToken(token.access_token)
  return token
}

export function getMe() {
  return apiRequest('/auth/me')
}

export function forgotPassword(email) {
  return apiRequest('/auth/forgot-password', { method: 'POST', body: { email } })
}

export function resetPassword(token, newPassword) {
  return apiRequest('/auth/reset-password', { method: 'POST', body: { token, new_password: newPassword } })
}
