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
  const [payments, setPayments] = useState([])

  useEffect(() => {
    getSiteSettings(locale)
      .then((s) => setSocial(SOCIAL.filter(([key]) => s[key]).map(([key, label]) => [label, s[key]])))
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

  return (
    <footer className="border-t border-gray-200 mt-12 py-10 px-4 text-sm text-gray-600">
      <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-5 gap-8">
        <div className="col-span-2 md:col-span-1">
          <p className="font-bold text-brand mb-1">MARU</p>
          <p>{t('footer.tagline')}</p>
          <NewsletterForm />
        </div>
        {columns.map((col) => (
          <nav key={col.titleKey} aria-label={t(col.titleKey)}>
            <p className="font-semibold text-gray-900 mb-2">{t(col.titleKey)}</p>
            <ul className="space-y-1.5">
              {col.links.map(([to, key]) => (
                <li key={key}><Link to={to}>{t(key)}</Link></li>
              ))}
            </ul>
          </nav>
        ))}
      </div>

      <div className="max-w-7xl mx-auto mt-8 border-t border-gray-200 pt-6 flex flex-wrap items-center justify-between gap-x-6 gap-y-3 text-xs text-gray-500">
        <p>
          &copy; {new Date().getFullYear()} MARU
          {' · '}
          <Link to="/privacy" className="underline">{t('footer.privacy')}</Link>
          {' · '}
          <Link to="/terms" className="underline">{t('footer.terms')}</Link>
          {' · '}
          <button type="button" onClick={openConsentSettings} className="underline">{t('consent.settings')}</button>
        </p>
        {payments.length > 0 && (
          <ul aria-label={t('footer.paymentMethods')} className="flex flex-wrap gap-2">
            {payments.map((name) => (
              <li key={name} className="border border-gray-300 rounded px-2 py-0.5">{name}</li>
            ))}
          </ul>
        )}
        {social.length > 0 && (
          <ul aria-label={t('footer.follow')} className="flex flex-wrap gap-3">
            {social.map(([label, url]) => (
              <li key={label}><a href={url} target="_blank" rel="noopener noreferrer" className="underline">{label}</a></li>
            ))}
          </ul>
        )}
      </div>
    </footer>
  )
}
