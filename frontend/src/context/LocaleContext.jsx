import { createContext, useContext, useState } from 'react'

export const LOCALES = ['ru', 'uz', 'en']
const LOCALE_KEY = 'maru_locale'

const LocaleContext = createContext(null)

export function LocaleProvider({ children }) {
  const [locale, setLocaleState] = useState(() => localStorage.getItem(LOCALE_KEY) || 'ru')

  const setLocale = (value) => {
    if (!LOCALES.includes(value)) return
    localStorage.setItem(LOCALE_KEY, value)
    setLocaleState(value)
  }

  return (
    <LocaleContext.Provider value={{ locale, setLocale }}>{children}</LocaleContext.Provider>
  )
}

export function useLocale() {
  const ctx = useContext(LocaleContext)
  if (!ctx) throw new Error('useLocale must be used within LocaleProvider')
  return ctx
}
