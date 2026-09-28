import { apiRequest } from './client'

export function listAboutSections(lang) {
  const qs = lang ? `?lang=${encodeURIComponent(lang)}` : ''
  return apiRequest(`/about-sections${qs}`)
}
