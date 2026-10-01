import { apiRequest } from '../api/client'

// Web push (PRD ТЗ№1 §38-39). The browser asks the visitor for permission, subscribes with the server's public key
// and we store the subscription so order updates and cart reminders can reach this device.

export function pushSupported() {
  return typeof window !== 'undefined' && 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
}

function urlBase64ToUint8Array(base64) {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4)
  const raw = atob((base64 + padding).replace(/-/g, '+').replace(/_/g, '/'))
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)))
}

async function registration() {
  return navigator.serviceWorker.register('/sw.js').then(() => navigator.serviceWorker.ready)
}

// 'unsupported' | 'unavailable' (server has no keys) | 'denied' | 'on' | 'off'
export async function pushState() {
  if (!pushSupported()) return 'unsupported'
  const { enabled } = await apiRequest('/push/public-key', { skipAuth: true })
  if (!enabled) return 'unavailable'
  if (Notification.permission === 'denied') return 'denied'
  const reg = await navigator.serviceWorker.getRegistration('/sw.js')
  const sub = reg ? await reg.pushManager.getSubscription() : null
  return sub ? 'on' : 'off'
}

export async function enablePush() {
  const { enabled, public_key: key } = await apiRequest('/push/public-key', { skipAuth: true })
  if (!enabled) throw new Error('unavailable')
  const permission = await Notification.requestPermission()
  if (permission !== 'granted') throw new Error('denied')
  const reg = await registration()
  const sub = (await reg.pushManager.getSubscription()) || (await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(key) }))
  const json = sub.toJSON()
  await apiRequest('/push/subscribe', { method: 'POST', body: { endpoint: json.endpoint, keys: json.keys } })
}

export async function disablePush() {
  const reg = await navigator.serviceWorker.getRegistration('/sw.js')
  const sub = reg ? await reg.pushManager.getSubscription() : null
  if (sub) {
    await apiRequest('/push/unsubscribe', { method: 'POST', body: { endpoint: sub.endpoint } }).catch(() => {})
    await sub.unsubscribe()
  }
}
