import { apiRequest } from './client'

export function subscribeNewsletter(email, locale) {
  return apiRequest('/newsletter/subscribe', { method: 'POST', body: { email, locale } })
}

export function confirmNewsletter(token) {
  return apiRequest('/newsletter/confirm', { method: 'POST', body: { token } })
}

export function unsubscribeNewsletter(token) {
  return apiRequest('/newsletter/unsubscribe', { method: 'POST', body: { token } })
}
