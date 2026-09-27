import { apiRequest } from './client'

export function listProducts(lang) {
  const qs = lang ? `?lang=${encodeURIComponent(lang)}` : ''
  return apiRequest(`/products/${qs}`)
}

export function getProduct(slug, lang) {
  const qs = lang ? `?lang=${encodeURIComponent(lang)}` : ''
  return apiRequest(`/products/${encodeURIComponent(slug)}${qs}`)
}
