import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { listPageSections } from '../api/pageSections'
import { listProducts } from '../api/products'
import { listFeaturedReviews } from '../api/reviews'
import FaqItem from '../components/FaqItem'
import { useCart } from '../context/CartContext'
import { useLocale } from '../context/LocaleContext'
import { VOLUMES_ML } from '../lib/navLinks'
import ProductCard from '../components/product/ProductCard'
import MarqueeHero from '../components/home/MarqueeHero'
import Reveal from '../components/home/Reveal'
import Seo from '../components/Seo'

const BENEFITS = ['benefitMaterial', 'benefitOwn', 'benefitRange', 'benefitQuality', 'benefitB2b', 'benefitExport']
const PACKS = [3, 5, 7]

// Bento layout for the six benefits (lg: 4 columns, A A B C / A A D D / E E F F).
const BENTO = [
  { cell: 'bg-brand text-white lg:col-span-2 lg:row-span-2 flex items-end min-h-[14rem]', text: 'text-white/85', big: true },
  { cell: 'bg-gray-50', text: 'text-gray-600' },
  { cell: 'bg-gray-50', text: 'text-gray-600' },
  { cell: 'bg-brand-light lg:col-span-2', text: 'text-gray-600' },
  { cell: 'bg-gray-50 lg:col-span-2 min-h-[11rem]', text: 'text-gray-600', photo: true },
  { cell: 'bg-brand-light lg:col-span-2', text: 'text-gray-600' },
]

function Section({ id, title, children, action }) {
  return (
    <section id={id} className="max-w-7xl mx-auto px-4 py-12 md:py-16" aria-labelledby={`${id}-title`}>
      <Reveal>
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <h2 id={`${id}-title`} className="text-3xl font-semibold tracking-tight md:text-4xl">{title}</h2>
          {action}
        </div>
        {children}
      </Reveal>
    </section>
  )
}

// Home page (PRD ТЗ№2 §8): value proposition and the fastest route to a purchase.
export default function Home() {
  const { t, locale } = useLocale()
  const { cart } = useCart()
  const currency = cart?.currency
  const location = useLocation()
  const [popular, setPopular] = useState([])
  const bestSellers = popular.slice(0, 4)
  const [reviews, setReviews] = useState([])
  const [faq, setFaq] = useState([])

  useEffect(() => {
    listProducts(locale, currency, { sort: 'popularity', limit: 12 }).then(setPopular).catch(() => {})
  }, [locale, currency])
  useEffect(() => {
    listFeaturedReviews(locale, 3).then(setReviews).catch(() => {})
    listPageSections('faq', locale).then((rows) => setFaq(rows.slice(0, 4))).catch(() => {})
  }, [locale])

  // Links such as /#sets scroll to their block.
  useEffect(() => {
    if (!location.hash) return
    const el = document.getElementById(location.hash.slice(1))
    if (el) el.scrollIntoView()
  }, [location.hash, bestSellers.length])

  // A second product photo for the bento and the manufacturing block.
  const photo = popular.map((p) => p.variants?.[0]?.images?.[0]?.image_url || p.variants?.[0]?.photo_url).filter(Boolean)[1] || null
  const heroImages = popular
    .map((p) => ({ src: p.variants?.[0]?.images?.[0]?.image_url || p.variants?.[0]?.photo_url }))
    .filter((i) => i.src)

  return (
    <div>
      <Seo
        jsonLd={{
          '@context': 'https://schema.org',
          '@type': 'Organization',
          name: 'MARU',
          url: typeof window !== 'undefined' ? window.location.origin : undefined,
        }}
      />

      {/* 8.2 Hero */}
      <MarqueeHero
        tagline={t('home.heroTag')}
        title={t('home.title')}
        description={t('home.subtitle')}
        primaryCta={t('home.cta')}
        secondaryCta={t('home.ctaBusiness')}
        images={heroImages}
      />

      {/* 8.3 Product categories: tile height follows the volume, so the row reads as a size scale */}
      <Section id="sizes" title={t('home.sizesTitle')}>
        <ul className="grid grid-cols-5 items-end gap-2 sm:gap-4">
          {VOLUMES_ML.map((ml) => (
            <li key={ml}>
              <Link
                to={`/shop?capacity=${ml}`}
                style={{ height: `${5 + (ml / 1900) * 7}rem` }}
                className="group flex flex-col items-center justify-end rounded-3xl bg-brand-light pb-4 text-center transition duration-base hover:-translate-y-1 hover:bg-brand"
              >
                <span className="text-lg font-semibold text-brand group-hover:text-white md:text-3xl">{ml}</span>
                <span className="text-xs text-gray-500 group-hover:text-white/80 md:text-sm">ml</span>
              </Link>
            </li>
          ))}
        </ul>
      </Section>

      {/* 8.4 Best sellers */}
      {bestSellers.length > 0 && (
        <Section
          id="bestsellers"
          title={t('home.bestSellers')}
          action={
            <Link to="/shop" className="rounded-full border border-brand px-5 py-2 text-sm font-medium text-brand transition hover:bg-brand-light">
              {t('dashboard.viewAll')}
            </Link>
          }
        >
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {bestSellers.map((p) => <ProductCard key={p.id} product={p} />)}
          </div>
        </Section>
      )}

      {/* 8.5 Why MARU: six benefits in a bento (lg: 4 columns, A A B C / A A D D / E E F F) */}
      <Section id="why" title={t('home.whyTitle')}>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {BENEFITS.map((key, i) => {
            const style = BENTO[i]
            const withPhoto = style.photo && photo
            return (
              <li key={key} className={`relative overflow-hidden rounded-3xl p-6 md:p-8 ${style.cell}`}>
                {withPhoto && (
                  <img src={photo} alt="" loading="lazy" className="absolute -right-6 -bottom-6 h-44 w-44 rounded-2xl bg-white object-contain p-3 opacity-90 shadow-md md:h-52 md:w-52" />
                )}
                <div className={`relative ${withPhoto ? 'max-w-[55%]' : ''}`}>
                  <h3 className={`font-semibold ${style.big ? 'mb-3 text-2xl md:text-3xl' : 'mb-1 text-lg'}`}>{t(`home.${key}`)}</h3>
                  <p className={`text-sm ${style.text}`}>{t(`home.${key}Text`)}</p>
                </div>
              </li>
            )
          })}
        </ul>
      </Section>

      {/* 8.6 Sets */}
      <Section id="sets" title={t('home.setsTitle')}>
        <div className="grid items-center gap-8 rounded-3xl bg-brand-light p-6 md:grid-cols-2 md:p-12">
          <p className="max-w-md text-lg text-gray-600">{t('home.setsText')}</p>
          <ul className="grid gap-3">
            {PACKS.map((n) => (
              <li key={n}>
                <Link
                  to="/shop"
                  className="flex items-center justify-between gap-4 rounded-2xl bg-white/95 px-6 py-4 transition duration-base hover:-translate-y-0.5 hover:shadow-token"
                >
                  <span className="text-xl font-semibold text-brand-dark">{t('home.pack', { n })}</span>
                  <span className="text-sm text-brand-dark/70">{t('home.packText', { n })}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </Section>

      {/* 8.7 B2B */}
      <section className="max-w-7xl mx-auto px-4 py-6">
        <Reveal>
          <div className="flex flex-wrap items-center justify-between gap-6 rounded-3xl bg-brand p-8 text-white md:p-12">
            <div className="max-w-2xl">
              <h2 className="mb-2 text-3xl font-semibold tracking-tight md:text-4xl">{t('home.b2bTitle')}</h2>
              <p className="text-white/85">{t('home.b2bText')}</p>
            </div>
            <Link to="/wholesale" className="inline-block whitespace-nowrap rounded-full bg-white/95 px-8 py-3 font-semibold text-brand-dark transition hover:scale-105 active:scale-95">
              {t('home.b2bCta')}
            </Link>
          </div>
        </Reveal>
      </section>

      {/* 8.8 Manufacturing and quality */}
      <Section id="manufacturing" title={t('home.manufacturingTitle')}>
        <div className={`grid items-center gap-8 ${photo ? 'md:grid-cols-2' : ''}`}>
          <div>
            <p className="mb-6 max-w-xl text-lg text-gray-600">{t('home.manufacturingText')}</p>
            <div className="flex flex-wrap gap-3">
              <Link to="/manufacturing" className="rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-dark">
                {t('home.learnMore')}
              </Link>
              <Link to="/quality" className="rounded-full border border-brand px-6 py-3 text-sm font-semibold text-brand transition hover:bg-brand-light">
                {t('footer.quality')}
              </Link>
            </div>
          </div>
          {photo && (
            <div className="flex aspect-[4/3] items-center justify-center rounded-3xl bg-brand-light p-8">
              <img src={photo} alt="" loading="lazy" className="h-full w-full object-contain" />
            </div>
          )}
        </div>
      </Section>

      {/* 8.9 Reviews: only shown once real approved reviews exist */}
      {reviews.length > 0 && (
        <Section id="reviews" title={t('home.reviewsTitle')}>
          <ul className="grid gap-4 md:grid-cols-3">
            {reviews.map((r, i) => (
              <li key={r.id} className={`rounded-3xl bg-gray-50 p-6 text-sm ${i === 1 ? 'md:mt-8' : ''}`}>
                <p className="mb-2 text-yellow-600" role="img" aria-label={t('product.ratingLabel', { avg: r.rating, n: 1 })}>
                  <span aria-hidden="true">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</span>
                </p>
                <p className="mb-4 whitespace-pre-wrap text-base text-gray-700">{r.content}</p>
                <p className="text-xs text-gray-500">
                  {r.author ? `${r.author} · ` : ''}
                  <Link to={`/products/${r.product_slug}`} className="underline">{r.product_name}</Link>
                </p>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* 8.10 FAQ */}
      {faq.length > 0 && (
        <section id="faq" className="max-w-7xl mx-auto px-4 py-12 md:py-16" aria-labelledby="faq-title">
          <Reveal className="grid gap-8 lg:grid-cols-[1fr_2fr]">
            <div>
              <h2 id="faq-title" className="mb-5 text-3xl font-semibold tracking-tight md:text-4xl">{t('home.faqTitle')}</h2>
              <Link to="/faq" className="inline-block rounded-full border border-brand px-5 py-2 text-sm font-medium text-brand transition hover:bg-brand-light">
                {t('home.allQuestions')}
              </Link>
            </div>
            <div>
              {faq.map((s) => <FaqItem key={s.id} question={s.title} answer={s.body} />)}
            </div>
          </Reveal>
        </section>
      )}

      {/* 8.11 Final CTA */}
      <section className="max-w-7xl mx-auto px-4 pt-6 pb-12 md:pb-16">
        <Reveal>
          <div className="rounded-3xl bg-brand-light px-6 py-14 text-center md:py-20">
            <h2 className="mb-6 text-3xl font-semibold tracking-tight md:text-4xl">{t('home.finalTitle')}</h2>
            <Link to="/shop" className="inline-block rounded-full bg-brand px-8 py-3 font-semibold text-white shadow-lg transition hover:scale-105 hover:bg-brand-dark active:scale-95">
              {t('home.finalCta')}
            </Link>
          </div>
        </Reveal>
      </section>
    </div>
  )
}
