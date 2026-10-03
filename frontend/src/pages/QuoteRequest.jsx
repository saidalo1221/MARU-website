import { useSearchParams } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'
import InquiryForm from '../components/forms/InquiryForm'
import PageIntro from '../components/layout/PageIntro'
import Seo from '../components/Seo'

const VALID_TYPES = new Set(['quote', 'wholesale', 'distributor'])

export default function QuoteRequest() {
  const { t } = useLocale()
  const [params] = useSearchParams()
  const requestedType = params.get('type')
  const defaultType = VALID_TYPES.has(requestedType) ? requestedType : 'quote'

  return (
    <div className="max-w-xl mx-auto px-4 py-12 md:py-16">
      <Seo title={t('quoteRequest.title')} />
      <PageIntro title={t('quoteRequest.title')} subtitle={t('quoteRequest.subtitle')} />
      <div className="rounded-3xl border border-gray-200 bg-gray-50 p-6 md:p-8">
        <InquiryForm defaultType={defaultType} initialProduct={params.get('product')} initialQuantity={params.get('quantity')} />
      </div>
    </div>
  )
}
