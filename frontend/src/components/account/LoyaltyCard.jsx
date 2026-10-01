import { useEffect, useState } from 'react'
import { apiRequest } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import { formatDate } from '../../lib/format'

// The signed-in customer's points: balance, the rules in one sentence, and the movements.
export default function LoyaltyCard() {
  const { t } = useLocale()
  const [data, setData] = useState(null)

  useEffect(() => {
    apiRequest('/loyalty/me').then(setData).catch(() => setData(null))
  }, [])

  if (!data || !data.enabled || !data.eligible) return null
  return (
    <section className="border border-gray-200 rounded-lg p-4 mb-6" aria-labelledby="loyalty-title">
      <div className="flex items-baseline justify-between mb-1">
        <h2 id="loyalty-title" className="font-semibold">{t('loyaltyAccount.title')}</h2>
        <p className="text-sm"><span className="text-gray-500">{t('loyaltyAccount.balance')}: </span><span className="text-xl font-semibold">{data.balance}</span></p>
      </div>
      {data.tier && <p className="text-sm font-medium mb-1">{t('loyaltyAccount.tier', { name: data.tier.name, x: data.tier.earn_multiplier })}</p>}
      {data.next_tier && <p className="text-xs text-gray-500 mb-1">{t('loyaltyAccount.nextTier', { n: data.next_tier.points_needed, name: data.next_tier.name })}</p>}
      {data.expiry_days > 0 && <p className="text-xs text-gray-500 mb-1">{t('loyaltyAccount.expiryNote', { days: data.expiry_days })}</p>}
      <p className="text-xs text-gray-500 mb-3">{t('loyaltyAccount.rules', { earn: data.earn_per_usd, value: data.value_usd, percent: data.max_redeem_percent })}</p>
      {data.history.length === 0 ? (
        <p className="text-sm text-gray-500">{t('loyaltyAccount.none')}</p>
      ) : (
        <ul className="divide-y divide-gray-100 text-sm">
          {data.history.slice(0, 8).map((h) => (
            <li key={h.id} className="flex justify-between gap-3 py-1.5">
              <span>{t(`loyaltyAccount.kind_${h.kind}`)} <span className="text-gray-500">· {formatDate(h.created_at)}</span></span>
              <span className={h.points > 0 ? 'text-green-700' : 'text-gray-700'}>{h.points > 0 ? `+${h.points}` : h.points}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
