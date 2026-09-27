import { apiRequest } from './client'

export function createQuote(payload) {
  return apiRequest('/quotes/', { method: 'POST', body: payload })
}
