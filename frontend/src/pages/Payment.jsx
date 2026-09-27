import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { getPaymentMethods } from '../api/orders'

export default function Payment() {
  const { t } = useLocale()
  const [methods, setMethods] = useState([])

  useEffect(() => {
    getPaymentMethods().then(setMethods).catch(() => {})
  }, [])

  const enabled = methods.filter((m) => m.enabled)

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-3">{t('payment.title')}</h1>
      <p className="text-gray-600 mb-8">{t('payment.subtitle')}</p>

      {enabled.length > 0 ? (
        <ul className="space-y-3">
          {enabled.map((m) => (
            <li key={m.id} className="border border-gray-200 rounded-lg p-4 flex items-center justify-between">
              <span className="font-medium">{m.display_name}</span>
              <span className="text-xs text-green-600">{t('payment.available')}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-gray-500">{t('payment.noneAvailable')}</p>
      )}

      <p className="text-sm text-gray-500 mt-8">{t('payment.note')}</p>
    </div>
  )
}
