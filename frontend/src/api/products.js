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

// One page of the catalogue, filtered and sorted by the server. Resolves to { data, total }.
export function queryProducts({ lang, currency, q, categoryIds, capacity, color, availability, priceMin, priceMax, sort, page = 1, limit = 12 } = {}) {
  const params = new URLSearchParams()
  if (lang) params.set('lang', lang)
  if (currency) params.set('currency', currency)
  if (q) params.set('q', q)
  if (categoryIds) params.set('category_ids', categoryIds)
  if (capacity) params.set('capacity', capacity)
  if (color) params.set('color', color)
  if (availability) params.set('availability', availability)
  if (priceMin !== undefined && priceMin !== '') params.set('price_min', priceMin)
  if (priceMax !== undefined && priceMax !== '') params.set('price_max', priceMax)
  if (sort && sort !== 'default') params.set('sort', sort)
  params.set('page', String(page))
  params.set('limit', String(limit))
  return apiRequest(`/products/?${params.toString()}`, { meta: true })
}

// The filter choices that exist (capacities, colours, categories); optionally within some categories.
export function getFacets(categoryIds) {
  return apiRequest(`/products/facets${categoryIds ? `?category_ids=${encodeURIComponent(categoryIds)}` : ''}`)
}

// Autocomplete: { products: [...], categories: [...] }.
export function suggestProducts(q, lang) {
  const params = new URLSearchParams({ q })
  if (lang) params.set('lang', lang)
  return apiRequest(`/products/suggest?${params.toString()}`)
}

export function getCategory(slug, lang) {
  return apiRequest(`/categories/${encodeURIComponent(slug)}${buildQuery({ lang })}`)
}

export function listCategories(lang) {
  return apiRequest(`/categories/${buildQuery({ lang })}`)
}

export function getProduct(slug, lang, currency) {
  return apiRequest(`/products/${encodeURIComponent(slug)}${buildQuery({ lang, currency })}`)
}
