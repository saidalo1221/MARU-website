import { useMemo, useSyncExternalStore } from 'react'

// Visitor consent (PRD ТЗ№3 §102). Nothing optional runs until the visitor
// opts in: "analytics" covers the storefront's behavioural events and the
// stored campaign/referrer attribution; "geo" covers sending the visitor's IP
// to a third-party geolocation service for the country/currency suggestion.
// Essential features (cart, login, checkout) never depend on this.
const KEY = 'maru_consent'
const CHANGED = 'maru:consent'
const OPEN = 'maru:consent-open'

// Used only when localStorage is blocked, so a choice still holds for the
// current page session (it just isn't remembered afterwards).
let memoryValue = null

function raw() {
  try {
    return localStorage.getItem(KEY) ?? memoryValue
  } catch {
    return memoryValue
  }
}

function parse(value) {
  try {
    const v = JSON.parse(value)
    if (v && typeof v === 'object') return { analytics: v.analytics === true, geo: v.geo === true }
  } catch {
    // fall through: treated as "not decided yet"
  }
  return null
}

export function getConsent() {
  return parse(raw())
}

export function hasConsent(kind) {
  return getConsent()?.[kind] === true
}

export function setConsent({ analytics, geo }) {
  const value = JSON.stringify({ analytics: !!analytics, geo: !!geo, at: Date.now() })
  memoryValue = value
  try {
    localStorage.setItem(KEY, value)
  } catch {
    // storage blocked: memoryValue still applies to this page session
  }
  window.dispatchEvent(new Event(CHANGED))
}

export function subscribeConsent(callback) {
  window.addEventListener(CHANGED, callback)
  window.addEventListener('storage', callback)
  return () => {
    window.removeEventListener(CHANGED, callback)
    window.removeEventListener('storage', callback)
  }
}

// null = the visitor has not chosen yet.
export function useConsent() {
  const value = useSyncExternalStore(subscribeConsent, raw, () => null)
  return useMemo(() => parse(value), [value])
}

// Lets the footer's "Cookie settings" link reopen the banner.
export function openConsentSettings() {
  window.dispatchEvent(new Event(OPEN))
}

export function onOpenConsentSettings(callback) {
  window.addEventListener(OPEN, callback)
  return () => window.removeEventListener(OPEN, callback)
}
