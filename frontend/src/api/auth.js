import { apiRequest, getDeviceId, setAccessToken } from './client'

export async function register(payload) {
  const token = await apiRequest('/auth/register', { method: 'POST', body: payload })
  setAccessToken(token.access_token)
  return token
}

// Returns either { access_token, ... } (known device — login complete) or
// { device_verification_required: true } (a code was emailed; the caller
// must collect it and call verifyLoginDevice()).
export async function login(email, password) {
  const result = await apiRequest('/auth/login', {
    method: 'POST',
    body: { email, password, device_id: getDeviceId() },
  })
  if (result.access_token) setAccessToken(result.access_token)
  return result
}

export async function verifyLoginDevice(email, code) {
  const token = await apiRequest('/auth/login/verify-device', {
    method: 'POST',
    body: { email, code, device_id: getDeviceId() },
  })
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

export function verifyEmail(token) {
  return apiRequest('/auth/verify-email', { method: 'POST', body: { token } })
}

export function resendVerification() {
  return apiRequest('/auth/resend-verification', { method: 'POST' })
}

export function updateProfile(payload) {
  return apiRequest('/auth/me', { method: 'PATCH', body: payload })
}

export function changePassword(currentPassword, newPassword) {
  return apiRequest('/auth/change-password', {
    method: 'POST',
    body: { current_password: currentPassword, new_password: newPassword },
  })
}
