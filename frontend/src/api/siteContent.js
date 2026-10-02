import { apiRequest } from './client'

// Public: admin-edited storefront text and per-page SEO tags for one language.
export function getContentOverrides(lang) {
  return apiRequest(`/content-overrides?lang=${encodeURIComponent(lang)}`)
}

export function getSeoMeta(lang) {
  return apiRequest(`/seo-meta?lang=${encodeURIComponent(lang)}`)
}

// Admin
export function adminListContentOverrides() {
  return apiRequest('/admin/content-overrides')
}
export function adminSaveContentOverrides(items) {
  return apiRequest('/admin/content-overrides', { method: 'PUT', body: { items } })
}
export function adminListSeoMeta() {
  return apiRequest('/admin/seo-meta')
}
export function adminSaveSeoMeta(payload) {
  return apiRequest('/admin/seo-meta', { method: 'PUT', body: payload })
}
