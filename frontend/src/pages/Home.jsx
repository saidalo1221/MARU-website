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
import Seo from '../components/Seo'

const BENEFITS = ['benefitMaterial', 'benefitOwn', 'benefitRange', 'benefitQuality', 'benefitB2b', 'benefitExport']
const PACKS = [3, 5, 7]

function Section({ id, title, children, action }) {
  return (
    <section id={id} className="max-w-7xl mx-auto px-4 py-10" aria-labelledby={`${id}-title`}>
      <div className="flex items-end justify-between gap-4 mb-5">
        <h2 id={`${id}-title`} className="text-2xl font-bold">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  )
}

// Home page (PRD ТЗ№2 §8): value proposition and the fastest route to a purchase.
export default function Home() {
  const { t, locale } = useLocale()
  const { cart } = useCart()
  const currency = cart?.currency
  const location = useLocation()
  const [bestSellers, setBestSellers] = useState([])
  const [reviews, setReviews] = useState([])
  const [faq, setFaq] = useState([])

  useEffect(() => {
    listProducts(locale, currency, { sort: 'popularity', limit: 4 }).then(setBestSellers).catch(() => {})
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

  const heroImage = bestSellers[0]?.variants?.[0]?.images?.[0]?.image_url || bestSellers[0]?.variants?.[0]?.photo_url

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
      <section className="bg-brand-light">
        <div className="max-w-7xl mx-auto px-4 py-14 grid md:grid-cols-2 gap-8 items-center">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold mb-4 text-gray-900">{t('home.title')}</h1>
            <p className="text-gray-700 mb-8">{t('home.subtitle')}</p>
            <div className="flex flex-wrap gap-3">
              <Link to="/shop" className="inline-block bg-brand text-white px-6 py-3 rounded font-medium hover:bg-brand-dark">
                {t('home.cta')}
              </Link>
              <Link to="/wholesale" className="inline-block border border-brand text-brand px-6 py-3 rounded font-medium">
                {t('home.ctaBusiness')}
              </Link>
            </div>
          </div>
          {heroImage && (
            <img src={heroImage} alt={bestSellers[0].name} className="w-full max-h-80 object-contain rounded-lg" />
          )}
        </div>
      </section>

      {/* 8.3 Product categories */}
      <Section id="sizes" title={t('home.sizesTitle')}>
        <ul className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {VOLUMES_ML.map((ml) => (
            <li key={ml}>
              <Link
                to={`/shop?capacity=${ml}`}
                className="block border border-gray-200 rounded-lg p-5 text-center hover:shadow-md transition"
              >
                <span className="block text-2xl font-bold text-brand">{ml}</span>
                <span className="text-sm text-gray-500">ml</span>
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
          action={<Link to="/shop" className="text-sm text-brand underline">{t('dashboard.viewAll')}</Link>}
        >
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {bestSellers.map((p) => <ProductCard key={p.id} product={p} />)}
          </div>
        </Section>
      )}

      {/* 8.5 Why MARU */}
      <Section id="why" title={t('home.whyTitle')}>
        <ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {BENEFITS.map((key) => (
            <li key={key} className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold mb-1">{t(`home.${key}`)}</h3>
              <p className="text-sm text-gray-600">{t(`home.${key}Text`)}</p>
            </li>
          ))}
        </ul>
      </Section>

      {/* 8.6 Sets */}
      <Section id="sets" title={t('home.setsTitle')}>
        <p className="text-gray-600 mb-4">{t('home.setsText')}</p>
        <ul className="grid sm:grid-cols-3 gap-3">
          {PACKS.map((n) => (
            <li key={n}>
              <Link to="/shop" className="block border border-gray-200 rounded-lg p-5 text-center hover:shadow-md transition">
                <span className="block text-xl font-bold text-brand">{t('home.pack', { n })}</span>
                <span className="text-sm text-gray-500">{t('home.packText', { n })}</span>
              </Link>
            </li>
          ))}
        </ul>
      </Section>

      {/* 8.7 B2B */}
      <section className="bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 py-10 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold mb-1">{t('home.b2bTitle')}</h2>
            <p className="text-gray-600">{t('home.b2bText')}</p>
          </div>
          <Link to="/wholesale" className="inline-block bg-brand text-white px-6 py-3 rounded font-medium hover:bg-brand-dark">
            {t('home.b2bCta')}
          </Link>
        </div>
      </section>

      {/* 8.8 Manufacturing and quality */}
      <Section id="manufacturing" title={t('home.manufacturingTitle')}>
        <p className="text-gray-600 mb-4 max-w-2xl">{t('home.manufacturingText')}</p>
        <div className="flex flex-wrap gap-4 text-sm">
          <Link to="/manufacturing" className="text-brand underline">{t('home.learnMore')}</Link>
          <Link to="/quality" className="text-brand underline">{t('footer.quality')}</Link>
        </div>
      </Section>

      {/* 8.9 Reviews: only shown once real approved reviews exist */}
      {reviews.length > 0 && (
        <Section id="reviews" title={t('home.reviewsTitle')}>
          <ul className="grid md:grid-cols-3 gap-4">
            {reviews.map((r) => (
              <li key={r.id} className="border border-gray-200 rounded-lg p-4 text-sm">
                <p className="text-yellow-600 mb-1" role="img" aria-label={t('product.ratingLabel', { avg: r.rating, n: 1 })}>
                  <span aria-hidden="true">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</span>
                </p>
                <p className="text-gray-700 mb-2 whitespace-pre-wrap">{r.content}</p>
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
        <Section
          id="faq"
          title={t('home.faqTitle')}
          action={<Link to="/faq" className="text-sm text-brand underline">{t('home.allQuestions')}</Link>}
        >
          <div className="max-w-3xl">
            {faq.map((s) => <FaqItem key={s.id} question={s.title} answer={s.body} />)}
          </div>
        </Section>
      )}

      {/* 8.11 Final CTA */}
      <section className="bg-brand-light">
        <div className="max-w-7xl mx-auto px-4 py-12 text-center">
          <h2 className="text-2xl font-bold mb-4">{t('home.finalTitle')}</h2>
          <Link to="/shop" className="inline-block bg-brand text-white px-6 py-3 rounded font-medium hover:bg-brand-dark">
            {t('home.finalCta')}
          </Link>
        </div>
      </section>
    </div>
  )
}
