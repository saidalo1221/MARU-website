import { useSearchParams } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'
import InquiryForm from '../components/forms/InquiryForm'

const VALID_TYPES = new Set(['quote', 'wholesale', 'distributor'])

export default function QuoteRequest() {
  const { t } = useLocale()
  const [params] = useSearchParams()
  const requestedType = params.get('type')
  const defaultType = VALID_TYPES.has(requestedType) ? requestedType : 'quote'

  return (
    <div className="max-w-lg mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">{t('quoteRequest.title')}</h1>
      <p className="text-sm text-gray-500 mb-6">{t('quoteRequest.subtitle')}</p>
      <InquiryForm defaultType={defaultType} />
    </div>
  )
}
