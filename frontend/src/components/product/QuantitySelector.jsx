export default function QuantitySelector({ value, min = 1, max, onChange }) {
  const clamp = (n) => Math.max(min, max ? Math.min(max, n) : n)

  return (
    <div className="flex items-center border border-gray-300 rounded w-fit">
      <button
        type="button"
        onClick={() => onChange(clamp(value - 1))}
        className="px-3 py-2 text-lg leading-none disabled:opacity-30"
        disabled={value <= min}
        aria-label="Decrease quantity"
      >
        −
      </button>
      <span className="px-4 min-w-[2.5rem] text-center">{value}</span>
      <button
        type="button"
        onClick={() => onChange(clamp(value + 1))}
        className="px-3 py-2 text-lg leading-none disabled:opacity-30"
        disabled={max !== undefined && value >= max}
        aria-label="Increase quantity"
      >
        +
      </button>
    </div>
  )
}
