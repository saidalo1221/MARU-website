import { Link } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'
import PageIntro from '../components/layout/PageIntro'
import Seo from '../components/Seo'

// Five points as a bento: one large green tile and four tinted ones (lg: A A / B C / D E).
const CELLS = ['bg-brand text-white md:col-span-2 min-h-[10rem] flex items-end text-2xl font-semibold', 'bg-brand-light', 'bg-gray-50', 'bg-gray-50', 'bg-brand-light']

export default function B2B() {
  const { t } = useLocale()
  const points = ['b2b.wholesale', 'b2b.bulkOrders', 'b2b.customQuantities', 'b2b.distributorOpportunities', 'b2b.internationalSupply']

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 md:py-16">
      <Seo title={t('b2b.title')} description={t('b2b.subtitle')} />
      <PageIntro title={t('b2b.title')} subtitle={t('b2b.subtitle')} />

      <ul className="mb-12 grid gap-4 md:grid-cols-2">
        {points.map((key, i) => (
          <li key={key} className={`rounded-3xl border border-gray-200 p-6 md:p-8 ${CELLS[i]}`}>
            {t(key)}
          </li>
        ))}
      </ul>

      <div className="text-center">
        <Link to="/quote" className="inline-block rounded-full bg-brand px-8 py-3 font-semibold text-white transition hover:bg-brand-dark active:scale-[0.98]">
          {t('quoteRequest.submit')}
        </Link>
      </div>
    </div>
  )
}
