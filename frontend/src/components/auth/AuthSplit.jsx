import { useEffect, useState } from 'react'
import { listProducts } from '../../api/products'
import { useLocale } from '../../context/LocaleContext'

const BENEFITS = ['benefitOwn', 'benefitMaterial', 'benefitQuality']

// Two-column layout for sign-in screens (layout from the 21st.dev sign-in component in design.md):
// form on the left, product photo with MARU's real selling points on the right (hidden on phones).
// The sample testimonials of the original are left out on purpose: no invented customers.
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

      <aside className="hidden md:flex flex-1 relative overflow-hidden rounded-3xl bg-brand-light items-end justify-center p-6" aria-hidden="true">
        {image && (
          <img src={image} alt="" className="absolute inset-0 h-full w-full object-contain p-16 pb-48" />
        )}
        <div className="relative flex w-full flex-col gap-3">
          {BENEFITS.map((key, i) => (
            <div
              key={key}
              className="maru-fade-up rounded-2xl border border-white/40 bg-white/70 p-4 text-sm leading-snug backdrop-blur"
              style={{ '--maru-delay': `${400 + i * 150}ms` }}
            >
              <p className="font-medium text-gray-900">{t(`home.${key}`)}</p>
              <p className="text-gray-600">{t(`home.${key}Text`)}</p>
            </div>
          ))}
        </div>
      </aside>
    </div>
  )
}

// Shared look for the form controls on these screens.
export const authInputClass =
  'w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3.5 text-sm transition-colors focus:border-brand focus:bg-brand-light focus:outline-none'
export const authButtonClass =
  'w-full rounded-2xl bg-brand py-3.5 font-medium text-white transition-colors hover:bg-brand-dark disabled:opacity-40'
