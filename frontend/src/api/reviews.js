import { apiRequest } from './client'

export function listReviews(slug) {
  return apiRequest(`/products/${encodeURIComponent(slug)}/reviews`)
}

export function createReview(slug, payload) {
  return apiRequest(`/products/${encodeURIComponent(slug)}/reviews`, { method: 'POST', body: payload })
}
