import { apiRequest } from './client'

export function listAddresses() {
  return apiRequest('/addresses/')
}

export function createAddress(payload) {
  return apiRequest('/addresses/', { method: 'POST', body: payload })
}

export function updateAddress(id, payload) {
  return apiRequest(`/addresses/${id}`, { method: 'PUT', body: payload })
}

export function deleteAddress(id) {
  return apiRequest(`/addresses/${id}`, { method: 'DELETE' })
}
