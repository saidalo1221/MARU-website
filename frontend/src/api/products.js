import { apiRequest } from './client'

function buildQuery({ lang, currency } = {}) {
  const params = new URLSearchParams()
  if (lang) params.set('lang', lang)
  if (currency) params.set('currency', currency)
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export function listProducts(lang, currency) {
  return apiRequest(`/products/${buildQuery({ lang, currency })}`)
}

export function getProduct(slug, lang, currency) {
  return apiRequest(`/products/${encodeURIComponent(slug)}${buildQuery({ lang, currency })}`)
}
