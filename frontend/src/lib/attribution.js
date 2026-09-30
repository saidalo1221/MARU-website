// Marketing attribution (PRD ТЗ№4 §18): remember where a visitor came from and
// send it with the order. utm_* params overwrite what was stored (latest
// campaign wins); otherwise the first visit's referrer/landing page is kept.
// Only the path is stored as the landing page, never the query string.
//
// Nothing is written to storage without analytics consent. The landing data
// is held in memory for the page session so a visitor who accepts a few
// seconds after arriving from a campaign link is still attributed.
import { hasConsent } from './consent'

const KEY = 'maru_attribution'
const UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']

let landing = null // in-memory only

function read() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || null
  } catch {
    return null
  }
}

function describeLanding() {
  const params = new URLSearchParams(window.location.search)
  const data = {}
  UTM_KEYS.forEach((k) => {
    const v = params.get(k)
    if (v) data[k] = v.slice(0, 255)
  })
  data.landing_page = window.location.pathname.slice(0, 255)
  if (document.referrer) {
    try {
      const ref = new URL(document.referrer)
      if (ref.origin !== window.location.origin) data.referrer = ref.origin + ref.pathname
    } catch {
      // ignore a malformed referrer
    }
  }
  return data
}

function hasUtm(data) {
  return UTM_KEYS.some((k) => data[k])
}

// Call at page load and again whenever consent changes.
export function captureAttribution() {
  if (!landing) landing = describeLanding()
  if (!hasConsent('analytics')) return
  try {
    if (read() && !hasUtm(landing)) return // keep the first visit's data
    localStorage.setItem(KEY, JSON.stringify(landing))
  } catch {
    // storage blocked: attribution is best-effort
  }
}

export function getAttribution() {
  return hasConsent('analytics') ? read() : null
}

// Called when analytics consent is withdrawn: forget everything.
export function clearAttribution() {
  landing = null
  try {
    localStorage.removeItem(KEY)
  } catch {
    // ignore
  }
}
