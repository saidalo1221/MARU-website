import { apiRequest } from './client'

export function listReviews(slug) {
  return apiRequest(`/products/${encodeURIComponent(slug)}/reviews`)
}

export function createReview(slug, payload) {
  return apiRequest(`/products/${encodeURIComponent(slug)}/reviews`, { method: 'POST', body: payload })
}

export function listFeaturedReviews(lang, limit = 6) {
  const params = new URLSearchParams({ limit: String(limit) })
  if (lang) params.set('lang', lang)
  return apiRequest(`/reviews/featured?${params.toString()}`)
}
