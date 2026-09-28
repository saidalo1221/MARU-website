import { Link } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'
import Seo from '../components/Seo'

export default function B2B() {
  const { t } = useLocale()
  const points = ['b2b.wholesale', 'b2b.bulkOrders', 'b2b.customQuantities', 'b2b.distributorOpportunities', 'b2b.internationalSupply']

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <Seo title={t('b2b.title')} description={t('b2b.subtitle')} />
      <h1 className="text-3xl font-bold mb-3">{t('b2b.title')}</h1>
      <p className="text-gray-600 mb-8">{t('b2b.subtitle')}</p>

      <ul className="grid sm:grid-cols-2 gap-4 mb-10">
        {points.map((key) => (
          <li key={key} className="border border-gray-200 rounded-lg p-4 text-sm">
            {t(key)}
          </li>
        ))}
      </ul>

      <Link to="/quote" className="inline-block bg-brand text-white px-6 py-3 rounded font-medium">
        {t('quoteRequest.submit')}
      </Link>
    </div>
  )
}
