import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { translations } from '../i18n/translations'

export const LOCALES = ['ru', 'uz', 'en']
const LOCALE_KEY = 'maru_locale'

export const LocaleContext = createContext(null)

function resolve(dict, path) {
  return path.split('.').reduce((node, key) => (node == null ? node : node[key]), dict)
}

function interpolate(template, vars) {
  if (!vars) return template
  return template.replace(/\{(\w+)\}/g, (match, key) => (key in vars ? String(vars[key]) : match))
}

export function LocaleProvider({ children }) {
  const [locale, setLocaleState] = useState(() => localStorage.getItem(LOCALE_KEY) || 'ru')

  // Keeps <html lang> in step with the UI language so screen readers pick the
  // right voice/pronunciation (WCAG 3.1.1); index.html only carries the default.
  useEffect(() => {
    document.documentElement.lang = locale
  }, [locale])

  const setLocale = (value) => {
    if (!LOCALES.includes(value)) return
    localStorage.setItem(LOCALE_KEY, value)
    setLocaleState(value)
  }

  // Static UI-text lookup (nav/buttons/form copy) — separate from the
  // backend-driven product name/description translations, which are fetched
  // via `?lang=` on the products API instead. Falls back to English, then to
  // the raw key, so a missing translation never renders blank.
  const t = useCallback(
    (key, vars) => {
      const value = resolve(translations[locale], key) ?? resolve(translations.en, key) ?? key
      return interpolate(value, vars)
    },
    [locale]
  )

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>{children}</LocaleContext.Provider>
  )
}

export function useLocale() {
  const ctx = useContext(LocaleContext)
  if (!ctx) throw new Error('useLocale must be used within LocaleProvider')
  return ctx
}
