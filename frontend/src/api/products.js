import { apiRequest } from './client'

function buildQuery({ lang, currency } = {}) {
  const params = new URLSearchParams()
  if (lang) params.set('lang', lang)
  if (currency) params.set('currency', currency)
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export function listProducts(lang, currency, { sort, limit } = {}) {
  const params = new URLSearchParams()
  if (lang) params.set('lang', lang)
  if (currency) params.set('currency', currency)
  if (sort) params.set('sort', sort)
  if (limit) params.set('limit', String(limit))
  const qs = params.toString()
  return apiRequest(`/products/${qs ? `?${qs}` : ''}`)
}

export function listCategories(lang) {
  return apiRequest(`/categories/${buildQuery({ lang })}`)
}

export function getProduct(slug, lang, currency) {
  return apiRequest(`/products/${encodeURIComponent(slug)}${buildQuery({ lang, currency })}`)
}
