import { apiRequest } from './client'

export function listPageSections(page, lang) {
  const params = new URLSearchParams({ page })
  if (lang) params.set('lang', lang)
  return apiRequest(`/page-sections?${params.toString()}`)
}
