import { Link } from 'react-router-dom'
import { useLocale } from '../../context/LocaleContext'
import NewsletterForm from './NewsletterForm'
import { openConsentSettings } from '../../lib/consent'

export default function Footer() {
  const { t } = useLocale()

  const columns = [
    {
      titleKey: 'footer.colShop',
      links: [
        ['/shop', 'header.shop'],
        ['/cart', 'header.cart'],
        ['/account/orders', 'footer.orders'],
      ],
    },
    {
      titleKey: 'footer.colBusiness',
      links: [
        ['/b2b', 'footer.b2b'],
        ['/wholesale', 'footer.wholesale'],
        ['/distributor', 'footer.distributor'],
        ['/quote', 'footer.requestQuote'],
      ],
    },
    {
      titleKey: 'footer.colCompany',
      links: [
        ['/about', 'footer.about'],
        ['/contact', 'footer.contact'],
        ['/blog', 'footer.blog'],
      ],
    },
    {
      titleKey: 'footer.colSupport',
      links: [
        ['/delivery', 'footer.delivery'],
        ['/payment', 'footer.payment'],
        ['/returns', 'footer.returns'],
        ['/track', 'footer.trackOrder'],
        ['/faq', 'footer.faq'],
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
                <li key={to}><Link to={to}>{t(key)}</Link></li>
              ))}
            </ul>
          </nav>
        ))}
      </div>
      <p className="max-w-7xl mx-auto mt-8 text-xs text-gray-500">
        &copy; {new Date().getFullYear()} MARU
        {' · '}
        <button type="button" onClick={openConsentSettings} className="underline">{t('consent.settings')}</button>
      </p>
    </footer>
  )
}
