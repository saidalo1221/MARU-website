import { useSyncExternalStore } from 'react'

// The visitor's delivery country (PRD ТЗ№2 §41): chosen in the header or the
// product page's delivery block, remembered across visits, and used as the
// default country at checkout. Empty string means "not chosen".
const KEY = 'maru_ship_country'
const listeners = new Set()

function read() {
  try {
    return localStorage.getItem(KEY) || ''
  } catch {
    return ''
  }
}

let current = read()

export function getShipCountry() {
  return current
}

export function setShipCountry(country) {
  current = country || ''
  try {
    if (current) localStorage.setItem(KEY, current)
    else localStorage.removeItem(KEY)
  } catch {
    // storage blocked: the choice just isn't remembered
  }
  listeners.forEach((listener) => listener())
}

function subscribe(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function useShipCountry() {
  return useSyncExternalStore(subscribe, () => current, () => '')
}
