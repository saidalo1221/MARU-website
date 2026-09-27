import { apiRequest } from './client'

export function getSiteSettings(lang) {
  const qs = lang ? `?lang=${encodeURIComponent(lang)}` : ''
  return apiRequest(`/site-settings${qs}`)
}
