import { apiRequest } from './client'

export function exportMyData() {
  return apiRequest('/privacy/export')
}

export function eraseMyAccount(password) {
  return apiRequest('/privacy/erase', { method: 'POST', body: { password, confirm: 'DELETE' } })
}
