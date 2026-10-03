// A tab strip (PRD §58 Tabs). `items` are { key, label }; the caller renders the
// panel for the active key. Left/right arrow keys move between tabs.
export default function Tabs({ items, active, onChange, label }) {
  const move = (e, index) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return
    e.preventDefault()
    const next = (index + (e.key === 'ArrowRight' ? 1 : items.length - 1)) % items.length
    onChange(items[next].key)
    e.currentTarget.parentElement.children[next]?.focus()
  }
  return (
    <div role="tablist" aria-label={label} className="flex gap-2">
      {items.map((item, i) => (
        <button
          key={item.key}
          type="button"
          role="tab"
          aria-selected={active === item.key}
          tabIndex={active === item.key ? 0 : -1}
          onClick={() => onChange(item.key)}
          onKeyDown={(e) => move(e, i)}
          className={`px-3 py-1 rounded text-sm border ${active === item.key ? 'bg-brand text-white border-brand' : 'border-gray-300'}`}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}
