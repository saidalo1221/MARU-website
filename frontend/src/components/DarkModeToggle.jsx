import { useTheme } from '../context/ThemeContext'
import { useLocale } from '../context/LocaleContext'

export default function DarkModeToggle() {
  const { theme, toggleTheme } = useTheme()
  const { t } = useLocale()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? t('theme.switchToLight') : t('theme.switchToDark')}
      title={isDark ? t('theme.switchToLight') : t('theme.switchToDark')}
      className="w-8 h-8 flex items-center justify-center rounded border border-gray-300 text-sm leading-none flex-shrink-0"
    >
      {isDark ? '☀️' : '🌙'}
    </button>
  )
}
