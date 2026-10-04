import { apiRequest } from './client'

export function listShippingCountries() {
  return apiRequest('/shipping/countries')
}

export function getShippingEstimate(country) {
  const qs = country ? `?country=${encodeURIComponent(country)}` : ''
  return apiRequest(`/shipping/estimate${qs}`)
}

export function listShippingMethods(country) {
  const qs = country ? `?country=${encodeURIComponent(country)}` : ''
  return apiRequest(`/shipping/methods${qs}`)
}
