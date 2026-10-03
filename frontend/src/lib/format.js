// Date formatting (PRD ТЗ№3 §72, §75): the API stores and returns UTC timestamps without
// a timezone marker ("2026-09-27T13:06:45"). JavaScript would read that as the visitor's
// LOCAL time and show the wrong hour, so it is parsed as UTC and then shown in the
// visitor's own timezone, with the site language's date conventions.
const LOCALE_KEY = 'maru_locale'
const LOCALE_TAGS = { ru: 'ru-RU', uz: 'uz-UZ', en: 'en-GB' }

function currentTag() {
  try {
    return LOCALE_TAGS[localStorage.getItem(LOCALE_KEY)] || LOCALE_TAGS.ru
  } catch {
    return LOCALE_TAGS.ru
  }
}

export function parseApiDate(value) {
  if (value instanceof Date) return value
  if (typeof value !== 'string') return new Date(value)
  // Add "Z" only when there is no offset already.
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value)
  return new Date(hasZone ? value : `${value}Z`)
}

export function formatDate(value, tag = currentTag()) {
  if (!value) return ''
  const d = parseApiDate(value)
  return Number.isNaN(d.getTime()) ? '' : new Intl.DateTimeFormat(tag, { dateStyle: 'medium' }).format(d)
}

export function formatDateTime(value, tag = currentTag()) {
  if (!value) return ''
  const d = parseApiDate(value)
  return Number.isNaN(d.getTime()) ? '' : new Intl.DateTimeFormat(tag, { dateStyle: 'medium', timeStyle: 'short' }).format(d)
}
