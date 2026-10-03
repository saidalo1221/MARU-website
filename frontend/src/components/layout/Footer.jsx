import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPaymentMethods } from '../../api/orders'
import { getSiteSettings } from '../../api/siteSettings'
import { useLocale } from '../../context/LocaleContext'
import NewsletterForm from './NewsletterForm'
import { openConsentSettings } from '../../lib/consent'

const SOCIAL = [
  ['facebook_url', 'Facebook'],
  ['instagram_url', 'Instagram'],
  ['telegram_url', 'Telegram'],
  ['youtube_url', 'YouTube'],
]

export default function Footer() {
  const { t, locale } = useLocale()
  const [social, setSocial] = useState([])
  const [contact, setContact] = useState({})
  const [payments, setPayments] = useState([])

  useEffect(() => {
    getSiteSettings(locale)
      .then((s) => {
        setSocial(SOCIAL.filter(([key]) => s[key]).map(([key, label]) => [label, s[key]]))
        setContact({ phone: s.phone, email: s.email })
      })
      .catch(() => {})
  }, [locale])

  // Only the payment methods that can actually be used are advertised.
  useEffect(() => {
    getPaymentMethods()
      .then((methods) => setPayments(methods.filter((m) => m.enabled).map((m) => m.display_name || m.id)))
      .catch(() => {})
  }, [])

  // Columns follow PRD ТЗ№2 §7: Shop, Business, Support, MARU.
  const columns = [
    {
      titleKey: 'footer.colShop',
      links: [
        ['/shop', 'header.allProducts'],
        ['/shop', 'header.containers'],
        ['/#sets', 'header.sets'],
        ['/shop?sort=newest', 'footer.newProducts'],
      ],
    },
    {
      titleKey: 'footer.colBusiness',
      links: [
        ['/wholesale', 'footer.wholesale'],
        ['/b2b', 'footer.b2b'],
        ['/distributor', 'footer.distributor'],
        ['/quote', 'footer.requestQuote'],
      ],
    },
    {
      titleKey: 'footer.colSupport',
      links: [
        ['/delivery', 'footer.delivery'],
        ['/payment', 'footer.payment'],
        ['/returns', 'footer.returns'],
        ['/faq', 'footer.faq'],
        ['/contact', 'footer.contact'],
        ['/track', 'footer.trackOrder'],
      ],
    },
    {
      titleKey: 'footer.colMaru',
      links: [
        ['/about', 'footer.about'],
        ['/manufacturing', 'footer.manufacturing'],
        ['/quality', 'footer.quality'],
        ['/blog', 'footer.blog'],
      ],
    },
  ]

  const linkCls = 'transition-colors hover:text-white hover:underline'

  // Deep forest block that closes the page; flat edge, text in warm off-white.
  return (
    <footer className="relative mt-20 bg-ink px-4 py-14 text-sm text-white/80">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-x-8 gap-y-10 lg:grid-cols-[1.4fr_repeat(4,1fr)]">
        <div className="col-span-2 lg:col-span-1">
          <p className="mb-2 text-2xl font-bold text-white">MARU</p>
          <p className="max-w-xs">{t('footer.tagline')}</p>
          {(contact.phone || contact.email) && (
            <ul className="mt-4 space-y-1">
              {contact.phone && <li><a href={`tel:${contact.phone.replace(/[^+\d]/g, '')}`} className={linkCls}>{contact.phone}</a></li>}
              {contact.email && <li><a href={`mailto:${contact.email}`} className={linkCls}>{contact.email}</a></li>}
            </ul>
          )}
          <NewsletterForm />
        </div>
        {columns.map((col) => (
          <nav key={col.titleKey} aria-label={t(col.titleKey)}>
            <p className="mb-3 font-semibold text-white">{t(col.titleKey)}</p>
            <ul className="space-y-2">
              {col.links.map(([to, key]) => (
                <li key={key}><Link to={to} className={linkCls}>{t(key)}</Link></li>
              ))}
            </ul>
          </nav>
        ))}
      </div>

      <div className="mx-auto mt-12 flex max-w-7xl flex-wrap items-center justify-between gap-x-6 gap-y-4 border-t border-white/15 pt-6 text-xs text-white/70">
        <p className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <span>&copy; {new Date().getFullYear()} MARU</span>
          <Link to="/privacy" className={linkCls}>{t('footer.privacy')}</Link>
          <Link to="/terms" className={linkCls}>{t('footer.terms')}</Link>
          <button type="button" onClick={openConsentSettings} className={linkCls}>{t('consent.settings')}</button>
        </p>
        {payments.length > 0 && (
          <ul aria-label={t('footer.paymentMethods')} className="flex flex-wrap gap-2">
            {payments.map((name) => (
              <li key={name} className="rounded-full border border-white/25 px-3 py-1">{name}</li>
            ))}
          </ul>
        )}
        {social.length > 0 && (
          <ul aria-label={t('footer.follow')} className="flex flex-wrap gap-4">
            {social.map(([label, url]) => (
              <li key={label}><a href={url} target="_blank" rel="noopener noreferrer" className={linkCls}>{label}</a></li>
            ))}
          </ul>
        )}
      </div>
    </footer>
  )
}
