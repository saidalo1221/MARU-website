import { apiRequest } from './client'

function buildQuery({ lang, category, limit } = {}) {
  const params = new URLSearchParams()
  if (lang) params.set('lang', lang)
  if (category) params.set('category', category)
  if (limit) params.set('limit', limit)
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export function listBlogCategories() {
  return apiRequest('/blog/categories')
}

export function listBlogPosts(lang, category, limit) {
  return apiRequest(`/blog/posts${buildQuery({ lang, category, limit })}`)
}

export function getBlogPost(slug, lang) {
  return apiRequest(`/blog/posts/${encodeURIComponent(slug)}${buildQuery({ lang })}`)
}
