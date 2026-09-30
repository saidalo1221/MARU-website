// Marketing attribution (PRD ТЗ№4 §18): remember where a visitor came from and
// send it with the order. utm_* params overwrite what was stored (latest
// campaign wins); otherwise the first visit's referrer/landing page is kept.
// Only the path is stored as the landing page, never the query string.
const KEY = 'maru_attribution'
const UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']

function read() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || null
  } catch {
    return null
  }
}

export function captureAttribution() {
  try {
    const params = new URLSearchParams(window.location.search)
    const utm = {}
    UTM_KEYS.forEach((k) => {
      const v = params.get(k)
      if (v) utm[k] = v.slice(0, 255)
    })
    const existing = read()
    if (existing && Object.keys(utm).length === 0) return

    const data = { ...utm, landing_page: window.location.pathname.slice(0, 255) }
    if (document.referrer) {
      try {
        const ref = new URL(document.referrer)
        if (ref.origin !== window.location.origin) data.referrer = ref.origin + ref.pathname
      } catch {
        // ignore a malformed referrer
      }
    }
    localStorage.setItem(KEY, JSON.stringify(data))
  } catch {
    // storage blocked: attribution is best-effort
  }
}

export function getAttribution() {
  return read()
}
