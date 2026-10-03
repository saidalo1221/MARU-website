import { useLocale } from '../../context/LocaleContext'

export default function QuantitySelector({ value, min = 1, max, onChange }) {
  const { t } = useLocale()
  const clamp = (n) => Math.max(min, max ? Math.min(max, n) : n)

  return (
    <div className="flex w-fit items-center rounded-full border border-gray-300 bg-white">
      <button
        type="button"
        onClick={() => onChange(clamp(value - 1))}
        className="px-4 py-2 text-lg leading-none disabled:opacity-30"
        disabled={value <= min}
        aria-label={t('product.decreaseQty')}
      >
        −
      </button>
      <span className="px-4 min-w-[2.5rem] text-center">{value}</span>
      <button
        type="button"
        onClick={() => onChange(clamp(value + 1))}
        className="px-4 py-2 text-lg leading-none disabled:opacity-30"
        disabled={max !== undefined && value >= max}
        aria-label={t('product.increaseQty')}
      >
        +
      </button>
    </div>
  )
}
