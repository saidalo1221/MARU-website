export default function VariantSelector({ variants, selectedVariantId, onSelect }) {
  return (
    <div>
      <p className="text-sm font-medium mb-2">Color</p>
      <div className="flex gap-2 flex-wrap">
        {variants.map((variant) => {
          const active = variant.id === selectedVariantId
          const disabled = !variant.is_active || variant.skus.every((s) => !s.is_active)
          return (
            <button
              key={variant.id}
              type="button"
              disabled={disabled}
              onClick={() => onSelect(variant.id)}
              title={variant.name}
              className={`w-9 h-9 rounded-full border-2 flex-shrink-0 ${
                active ? 'border-brand' : 'border-gray-300'
              } ${disabled ? 'opacity-30 cursor-not-allowed' : ''}`}
              style={{ backgroundColor: variant.color_hex || '#ddd' }}
              aria-label={variant.name}
              aria-pressed={active}
            />
          )
        })}
      </div>
    </div>
  )
}
