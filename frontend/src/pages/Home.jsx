import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, useReducedMotion, useScroll, useTransform } from 'framer-motion'
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
import CountUp from '../components/motion/CountUp'
import Magnetic from '../components/motion/Magnetic'
import ScrollProgress from '../components/motion/ScrollProgress'
import Spotlight from '../components/motion/Spotlight'
import TiltCard from '../components/motion/TiltCard'
import VelocityMarquee from '../components/motion/VelocityMarquee'
import WordReveal from '../components/motion/WordReveal'
import Seo from '../components/Seo'

const BENEFITS = ['benefitMaterial', 'benefitOwn', 'benefitRange', 'benefitQuality', 'benefitB2b', 'benefitExport']
const PACKS = [3, 5, 7]

// Staggered entrance shared by the tile groups: each item springs up once, in order (hierarchy: reading order).
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }
const rise = { hidden: { opacity: 0, y: 28 }, show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 140, damping: 20 } } }
const slideIn = { hidden: { opacity: 0, x: -24 }, show: { opacity: 1, x: 0, transition: { type: 'spring', stiffness: 140, damping: 20 } } }

// Bento layout for the six benefits (lg: 4 columns, two even rows: A A B C / D E E F). No tile is taller
// than its text needs, so there is no empty space inside a tile.
const BENTO = [
  { cell: 'bg-brand text-white flex flex-col justify-center', span: 'lg:col-span-2', text: 'text-white/90', big: true },
  { cell: 'bg-brand-light', text: 'text-gray-600' },
  { cell: 'bg-gray-50 border border-gray-200', text: 'text-gray-600' },
  { cell: 'bg-gray-50 border border-gray-200', text: 'text-gray-600' },
  { cell: 'bg-gray-50 border border-gray-200', span: 'lg:col-span-2', text: 'text-gray-600', photo: true },
  { cell: 'bg-brand-light', text: 'text-gray-600' },
]

function Section({ id, title, children, action }) {
  return (
    <section id={id} className="max-w-7xl mx-auto px-4 py-12 md:py-16" aria-labelledby={`${id}-title`}>
      <Reveal>
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <h2 id={`${id}-title`} className="text-3xl font-semibold tracking-tight md:text-4xl"><WordReveal text={title} /></h2>
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
  const reduce = useReducedMotion()
  // the dark manufacturing panel grows into place as it scrolls into view
  const mfgRef = useRef(null)
  const { scrollYProgress: mfgProgress } = useScroll({ target: mfgRef, offset: ['start end', 'start 0.35'] })
  const mfgScale = useTransform(mfgProgress, [0, 1], [0.93, 1])
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
      <ScrollProgress />
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
        <motion.ul
          className="grid grid-cols-5 items-end gap-2 sm:gap-4"
          variants={stagger}
          initial={reduce ? false : 'hidden'}
          whileInView="show"
          viewport={{ once: true, amount: 0.3 }}
        >
          {VOLUMES_ML.map((ml) => (
            <motion.li key={ml} variants={rise}>
              <Link
                to={`/shop?capacity=${ml}`}
                style={{ height: `${5 + (ml / 1900) * 7}rem` }}
                className="group flex flex-col items-center justify-end rounded-3xl bg-brand-light pb-4 text-center transition duration-base hover:-translate-y-1 hover:bg-brand"
              >
                <span className="text-lg font-semibold text-brand group-hover:text-white md:text-3xl">{ml}</span>
                <span className="text-xs text-gray-500 group-hover:text-white/80 md:text-sm">ml</span>
              </Link>
            </motion.li>
          ))}
        </motion.ul>
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
            {bestSellers.map((p) => (
              <TiltCard key={p.id} className="h-full">
                <ProductCard product={p} />
              </TiltCard>
            ))}
          </div>
        </Section>
      )}

      {/* Moving text band: drifts by itself and reacts to the scroll speed */}
      <div className="overflow-hidden py-6 md:py-10">
        <VelocityMarquee items={[t('home.heroTag'), t('home.manufacturingTitle')]} base={-3} className="text-4xl font-semibold tracking-tight text-gray-900 md:text-7xl" />
        <VelocityMarquee items={[`${VOLUMES_ML.join(' · ')} ml`]} base={3} outline className="mt-3 text-4xl font-semibold tracking-tight text-gray-400 md:mt-5 md:text-7xl" />
      </div>

      {/* 8.5 Why MARU: six benefits in a bento (lg: 4 columns, A A B C / D E E F) */}
      <Section id="why" title={t('home.whyTitle')}>
        <motion.ul
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
          variants={stagger}
          initial={reduce ? false : 'hidden'}
          whileInView="show"
          viewport={{ once: true, amount: 0.2 }}
        >
          {BENEFITS.map((key, i) => {
            const style = BENTO[i]
            const withPhoto = style.photo && photo
            return (
              <motion.li key={key} variants={rise} className={style.span || ''}>
                <Spotlight
                  className={`h-full rounded-3xl p-6 md:p-8 ${style.cell} ${withPhoto ? 'min-h-[11rem]' : ''}`}
                  color={style.big ? 'rgb(255 255 255 / 0.22)' : 'rgb(200 60 30 / 0.10)'}
                >
                {withPhoto && (
                  <img src={photo} alt="" loading="lazy" className="absolute -right-6 -bottom-6 h-44 w-44 rounded-2xl bg-white object-contain p-3 opacity-90 shadow-md md:h-52 md:w-52" />
                )}
                <div className={`relative ${withPhoto ? 'max-w-[55%]' : ''}`}>
                  <h3 className={`font-semibold ${style.big ? 'mb-2 text-2xl md:text-3xl' : 'mb-1 text-lg'}`}>{t(`home.${key}`)}</h3>
                  <p className={`${style.big ? 'text-base' : 'text-sm'} ${style.text}`}>{t(`home.${key}Text`)}</p>
                </div>
                </Spotlight>
              </motion.li>
            )
          })}
        </motion.ul>
      </Section>

      {/* 8.6 Sets */}
      <Section id="sets" title={t('home.setsTitle')}>
        <div className="grid items-center gap-8 rounded-3xl bg-brand-light p-6 md:grid-cols-2 md:p-12">
          <p className="max-w-md text-lg text-gray-600">{t('home.setsText')}</p>
          <motion.ul
            className="grid gap-3"
            variants={stagger}
            initial={reduce ? false : 'hidden'}
            whileInView="show"
            viewport={{ once: true, amount: 0.4 }}
          >
            {PACKS.map((n) => (
              <motion.li key={n} variants={slideIn}>
                <Link
                  to="/shop"
                  className="group flex items-center justify-between gap-4 rounded-2xl bg-white/95 px-6 py-4 transition duration-base hover:-translate-y-0.5 hover:shadow-token"
                >
                  <span className="text-xl font-semibold text-ink">{t('home.pack', { n })}</span>
                  <span className="flex items-center gap-3 text-sm text-ink/70">
                    {t('home.packText', { n })}
                    <span aria-hidden="true" className="inline-block text-brand transition-transform duration-base group-hover:translate-x-1.5">&rarr;</span>
                  </span>
                </Link>
              </motion.li>
            ))}
          </motion.ul>
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
            <Magnetic>
              <Link to="/wholesale" className="inline-block whitespace-nowrap rounded-full bg-white/95 px-8 py-3 font-semibold text-ink transition hover:scale-105 active:scale-95">
                {t('home.b2bCta')}
              </Link>
            </Magnetic>
          </div>
        </Reveal>
      </section>

      {/* 8.8 Manufacturing and quality: dark panel, the facts that are true today (own production, material,
          clear specifications) plus two figures that come straight from the size list. */}
      <section ref={mfgRef} id="manufacturing" className="max-w-7xl mx-auto px-4 py-12 md:py-16" aria-labelledby="manufacturing-title">
        <Reveal>
          <motion.div style={reduce ? undefined : { scale: mfgScale }}>
          <Spotlight color="rgb(255 255 255 / 0.10)" className={`grid items-stretch gap-8 rounded-3xl bg-ink p-6 text-white md:p-12 ${photo ? 'lg:grid-cols-[1.2fr_1fr]' : ''}`}>
            <div className="flex flex-col">
              <h2 id="manufacturing-title" className="mb-4 text-3xl font-semibold tracking-tight md:text-4xl">{t('home.manufacturingTitle')}</h2>
              <p className="mb-8 max-w-xl text-lg text-white/80">{t('home.manufacturingText')}</p>

              <ul className="mb-8 space-y-3 text-white/80">
                {['benefitOwnText', 'benefitMaterialText', 'benefitQualityText'].map((key) => (
                  <li key={key} className="border-l-2 border-brand pl-4">{t(`home.${key}`)}</li>
                ))}
              </ul>

              <dl className="mb-8 grid grid-cols-2 gap-4">
                <div className="rounded-2xl bg-white/10 p-5">
                  <dd className="text-4xl font-semibold"><CountUp to={VOLUMES_ML.length} /></dd>
                  <dt className="mt-1 text-sm text-white/70">{t('home.statSizes')}</dt>
                </div>
                <div className="rounded-2xl bg-white/10 p-5">
                  <dd className="text-3xl font-semibold md:text-4xl"><CountUp to={VOLUMES_ML[0]} />-<CountUp to={VOLUMES_ML[VOLUMES_ML.length - 1]} /><span className="ml-1 text-base font-normal text-white/70">ml</span></dd>
                  <dt className="mt-1 text-sm text-white/70">{t('home.statRange')}</dt>
                </div>
              </dl>

              <div className="mt-auto flex flex-wrap gap-3">
                <Link to="/manufacturing" className="rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-dark active:scale-[0.98]">
                  {t('home.learnMore')}
                </Link>
                <Link to="/quality" className="rounded-full border border-white/40 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10">
                  {t('footer.quality')}
                </Link>
              </div>
            </div>
            {photo && (
              <div className="flex min-h-[16rem] items-center justify-center rounded-3xl bg-white p-8">
                <img src={photo} alt="" loading="lazy" className="max-h-[22rem] w-full object-contain" />
              </div>
            )}
          </Spotlight>
          </motion.div>
        </Reveal>
      </section>

      {/* 8.9 Reviews: only shown once real approved reviews exist */}
      {reviews.length > 0 && (
        <Section id="reviews" title={t('home.reviewsTitle')}>
          <motion.ul className="grid gap-4 md:grid-cols-3" variants={stagger} initial={reduce ? false : 'hidden'} whileInView="show" viewport={{ once: true, amount: 0.2 }}>
            {reviews.map((r, i) => (
              <motion.li key={r.id} variants={rise} className={`rounded-3xl bg-gray-50 p-6 text-sm ${i === 1 ? 'md:mt-8' : ''}`}>
                <p className="mb-2 text-yellow-600" role="img" aria-label={t('product.ratingLabel', { avg: r.rating, n: 1 })}>
                  <span aria-hidden="true">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</span>
                </p>
                <p className="mb-4 whitespace-pre-wrap text-base text-gray-700">{r.content}</p>
                <p className="text-xs text-gray-500">
                  {r.author ? `${r.author} · ` : ''}
                  <Link to={`/products/${r.product_slug}`} className="underline">{r.product_name}</Link>
                </p>
              </motion.li>
            ))}
          </motion.ul>
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
            <h2 className="mb-6 text-3xl font-semibold tracking-tight md:text-4xl"><WordReveal text={t('home.finalTitle')} /></h2>
            <Magnetic strength={0.35}>
              <Link to="/shop" className="inline-block rounded-full bg-brand px-8 py-3 font-semibold text-white shadow-lg transition hover:scale-105 hover:bg-brand-dark active:scale-95">
                {t('home.finalCta')}
              </Link>
            </Magnetic>
          </div>
        </Reveal>
      </section>
    </div>
  )
}
