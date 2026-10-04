import { useLocale } from '../../context/LocaleContext'

// Star rating with a text alternative (PRD §58 Rating): "★ 4.5 (12)".
export default function Rating({ value, count, className = '' }) {
  const { t } = useLocale()
  if (!count) return null
  return (
    <p className={`text-xs text-yellow-600 ${className}`} role="img" aria-label={t('product.ratingLabel', { avg: value, n: count })}>
      <span aria-hidden="true">★ {value} ({count})</span>
    </p>
  )
}
