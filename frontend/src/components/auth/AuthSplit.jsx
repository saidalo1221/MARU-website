import { useEffect, useState } from 'react'
import { listProducts } from '../../api/products'
import { useLocale } from '../../context/LocaleContext'
import { VOLUMES_ML } from '../../lib/navLinks'

const BENEFITS = ['benefitOwn', 'benefitMaterial', 'benefitQuality']

// Brand gradient for the side panel: vermilion glow in the top corner fading through deep red into ink.
// Colours come from the tokens, so a palette change restyles it too.
const PANEL_BG = [
  'radial-gradient(90% 60% at 100% 0%, rgb(var(--color-brand) / 0.9) 0%, transparent 70%)',
  'linear-gradient(165deg, rgb(var(--color-brand)) 0%, rgb(var(--color-brand-dark)) 52%, rgb(var(--color-ink)) 100%)',
].join(', ')

// Two-column layout for sign-in screens (layout from the 21st.dev sign-in component in design.md):
// form on the left, a brand gradient panel on the right with the wordmark, a product photo and MARU's real
// selling points (hidden on phones). The sample testimonials of the original are left out on purpose.
export default function AuthSplit({ title, description, children }) {
  const { t, locale } = useLocale()
  const [image, setImage] = useState(null)

  useEffect(() => {
    listProducts(locale, undefined, { sort: 'popularity', limit: 8 })
      .then((rows) => {
        const urls = rows.map((p) => p.variants?.[0]?.images?.[0]?.image_url || p.variants?.[0]?.photo_url)
        setImage(urls.find(Boolean) || null)
      })
      .catch(() => {})
  }, [locale])

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 md:py-8 flex flex-col md:flex-row gap-6 md:min-h-[calc(100dvh-8rem)]">
      <section className="flex-1 flex items-center justify-center py-6 md:py-0">
        <div className="w-full max-w-md">
          <h1 className="maru-fade-up text-4xl md:text-5xl font-semibold tracking-tight text-gray-900" style={{ '--maru-delay': '0ms' }}>
            {title}
          </h1>
          {description && (
            <p className="maru-fade-up mt-3 text-gray-600" style={{ '--maru-delay': '100ms' }}>{description}</p>
          )}
          <div className="maru-fade-up mt-8" style={{ '--maru-delay': '200ms' }}>{children}</div>
        </div>
      </section>

      <aside
        className="relative hidden flex-1 flex-col justify-between overflow-hidden rounded-3xl p-8 text-white md:flex"
        style={{ background: PANEL_BG }}
        aria-hidden="true"
      >
        {/* soft light shapes for depth */}
        <span className="pointer-events-none absolute -left-24 top-1/3 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
        <span className="pointer-events-none absolute -right-16 bottom-10 h-64 w-64 rounded-full bg-black/20 blur-3xl" />

        <div className="relative flex items-start justify-between gap-6">
          <div>
            <p className="text-3xl font-bold tracking-tight">MARU</p>
            <p className="mt-1 max-w-[16rem] text-sm text-white/80">{t('footer.tagline')}</p>
          </div>
          {image && (
            <div className="-mr-2 w-40 rotate-3 rounded-3xl bg-white p-3 shadow-xl">
              <img src={image} alt="" className="aspect-square w-full rounded-2xl object-contain" />
            </div>
          )}
        </div>

        {/* the size scale, as on the home page: tiles grow with the volume */}
        <div className="relative my-8">
          <p className="mb-4 text-lg font-semibold">{t('home.sizesTitle')}</p>
          <ul className="flex items-end gap-2">
            {VOLUMES_ML.map((ml) => (
              <li
                key={ml}
                style={{ height: `${4 + (ml / 1900) * 7}rem` }}
                className="flex flex-1 flex-col items-center justify-end rounded-2xl border border-white/25 bg-white/15 pb-3 backdrop-blur"
              >
                <span className="text-lg font-semibold">{ml}</span>
                <span className="text-xs text-white/75">ml</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="relative flex flex-col gap-3">
          {BENEFITS.map((key, i) => (
            <div
              key={key}
              className="maru-fade-up rounded-2xl border border-white/20 bg-white/10 p-4 text-sm leading-snug backdrop-blur"
              style={{ '--maru-delay': `${400 + i * 150}ms` }}
            >
              <p className="font-medium">{t(`home.${key}`)}</p>
              <p className="text-white/80">{t(`home.${key}Text`)}</p>
            </div>
          ))}
        </div>
      </aside>
    </div>
  )
}

// Shared look for the form controls on these screens.
export const authInputClass =
  'w-full rounded-2xl border border-gray-300 bg-white px-4 py-3.5 text-sm transition-colors focus:border-brand focus:outline-none'
export const authButtonClass =
  'w-full rounded-full bg-brand py-3.5 font-semibold text-white transition-colors hover:bg-brand-dark disabled:opacity-40'
