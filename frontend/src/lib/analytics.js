import { apiRequest, getDeviceId } from '../api/client'

// Fire-and-forget: analytics must never surface an error or slow the UI.
// Device id doubles as the anonymous session id (user_id is attached
// server-side from the auth token when present).
export function trackEvent(eventName, properties = {}) {
  try {
    apiRequest('/analytics/events', {
      method: 'POST',
      body: { event_name: eventName, session_id: getDeviceId(), properties },
    }).catch(() => {})
  } catch {
    // ignore
  }
}
