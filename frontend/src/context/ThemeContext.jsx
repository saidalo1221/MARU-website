import { createContext, useCallback, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext(null)
const STORAGE_KEY = 'maru_theme'
const PREFERENCES = ['system', 'light', 'dark']

function getInitialPreference() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (PREFERENCES.includes(stored)) return stored
  } catch {
    // localStorage unavailable (private mode etc.): follow the system.
  }
  return 'system'
}

function systemPrefersDark() {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
}

// `preference` is what the visitor picked (system | light | dark); `theme` is what is actually shown
// (light | dark). With "system" the theme follows the operating system, also while the page is open.
export function ThemeProvider({ children }) {
  const [preference, setPreference] = useState(getInitialPreference)
  const [systemDark, setSystemDark] = useState(systemPrefersDark)

  useEffect(() => {
    const query = window.matchMedia?.('(prefers-color-scheme: dark)')
    if (!query) return undefined
    const onChange = (e) => setSystemDark(e.matches)
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [])

  const theme = preference === 'system' ? (systemDark ? 'dark' : 'light') : preference

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, preference)
    } catch {
      // ignore: worst case the choice doesn't persist across visits
    }
  }, [preference])

  const toggleTheme = useCallback(() => {
    setPreference(theme === 'dark' ? 'light' : 'dark')
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, preference, setPreference, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
