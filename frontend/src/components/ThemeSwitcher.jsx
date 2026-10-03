import { useTheme } from '../context/ThemeContext'
import { useLocale } from '../context/LocaleContext'

// Text glyphs rather than emoji (︎ forces the text form of the sun) so they take the colour of the button.
const OPTIONS = [
  { value: 'system', glyph: '◐', labelKey: 'theme.system' },
  { value: 'light', glyph: '☀︎', labelKey: 'theme.light' },
  { value: 'dark', glyph: '☾', labelKey: 'theme.dark' },
]

// System / light / dark as one segmented pill with a sliding highlight (layout after the 21st.dev
// "theme switcher", design.md). The highlight moves with transform only.
export default function ThemeSwitcher() {
  const { preference, setPreference } = useTheme()
  const { t } = useLocale()
  const index = Math.max(0, OPTIONS.findIndex((o) => o.value === preference))

  return (
    <div
      role="radiogroup"
      aria-label={t('theme.label')}
      className="relative inline-flex flex-shrink-0 rounded-full border border-gray-300 bg-white/70 p-0.5"
    >
      <span
        aria-hidden="true"
        className="absolute left-0.5 top-0.5 h-6 w-6 rounded-full bg-brand transition-transform duration-base"
        style={{ transform: `translateX(${index * 100}%)` }}
      />
      {OPTIONS.map((o) => {
        const active = o.value === preference
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={t(o.labelKey)}
            title={t(o.labelKey)}
            onClick={() => setPreference(o.value)}
            className={`relative z-10 flex h-6 w-6 items-center justify-center rounded-full text-sm leading-none transition-colors ${
              active ? 'text-white' : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            {o.glyph}
          </button>
        )
      })}
    </div>
  )
}
