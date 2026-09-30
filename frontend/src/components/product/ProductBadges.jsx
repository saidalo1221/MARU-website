import { useLocale } from '../../context/LocaleContext'

// Renders the New / Sale / Best Seller / Out of Stock ribbons for a product.
// `badges` is the `badges` object the backend attaches to every ProductOut
// (see app/services/badges.py) — never computed here, so admin auto/manual
// mode stays a single source of truth.
export default function ProductBadges({ badges, className = '' }) {
  const { t } = useLocale()
  if (!badges) return null

  const items = [
    badges.is_new && { key: 'new', label: t('product.badgeNew'), cls: 'bg-blue-600 text-white' },
    badges.is_sale && { key: 'sale', label: t('product.badgeSale'), cls: 'bg-red-600 text-white' },
    badges.is_bestseller && { key: 'bestseller', label: t('product.badgeBestseller'), cls: 'bg-amber-700 text-white' },
    badges.is_out_of_stock && { key: 'oos', label: t('product.badgeOutOfStock'), cls: 'bg-gray-700 text-white' },
  ].filter(Boolean)

  if (items.length === 0) return null

  return (
    <div className={`flex flex-wrap gap-1 ${className}`}>
      {items.map((item) => (
        <span key={item.key} className={`text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded ${item.cls}`}>
          {item.label}
        </span>
      ))}
    </div>
  )
}
