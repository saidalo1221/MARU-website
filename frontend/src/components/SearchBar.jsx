import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'
import { useShipCountry } from '../lib/shipCountry'
import { suggestProducts } from '../api/products'

// Search with autocomplete (PRD ТЗ№2 §18): product and category suggestions,
// SKU codes and sizes, typo tolerance. Fully keyboard operable (combobox pattern).
export default function SearchBar({ className = '' }) {
  const { locale, t } = useLocale()
  const shipCountry = useShipCountry()
  const [value, setValue] = useState('')
  const [suggestions, setSuggestions] = useState({ products: [], categories: [] })
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const navigate = useNavigate()
  const containerRef = useRef(null)
  const listId = useId()

  // The server does the matching (name, SKU, category, size, typos), so the browser never holds the catalogue.
  // Debounced, and answers that arrive after the visitor typed more are dropped.
  useEffect(() => {
    const query = value.trim()
    if (!query) {
      setSuggestions({ products: [], categories: [] })
      return undefined
    }
    let current = true
    const id = setTimeout(() => {
      suggestProducts(query, locale)
        .then((r) => current && setSuggestions(r))
        .catch(() => current && setSuggestions({ products: [], categories: [] }))
    }, 250)
    return () => {
      current = false
      clearTimeout(id)
    }
  }, [value, locale, shipCountry])

  useEffect(() => {
    const onClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const options = useMemo(() => {
    const query = value.trim()
    if (!query) return []
    const items = [
      ...suggestions.products.map((p) => ({ type: 'product', key: `p${p.id}`, label: p.name, hint: `${p.volume_ml} ml`, to: `/products/${p.slug}` })),
      ...suggestions.categories.map((c) => ({ type: 'category', key: `c${c.id}`, label: c.name, hint: t('search.category'), to: `/shop?category=${c.id}` })),
    ]
    items.push({ type: 'all', key: 'all', label: t('search.seeAll', { query }), to: `/search?q=${encodeURIComponent(query)}` })
    return items
  }, [suggestions, value, t])

  const go = (to) => {
    setOpen(false)
    setActive(-1)
    navigate(to)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (active >= 0 && options[active]) {
      go(options[active].to)
      if (options[active].type !== 'all') setValue('')
      return
    }
    if (value.trim()) go(`/search?q=${encodeURIComponent(value.trim())}`)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setOpen(false)
      setActive(-1)
    } else if (e.key === 'ArrowDown' && options.length) {
      e.preventDefault()
      setOpen(true)
      setActive((i) => (i + 1) % options.length)
    } else if (e.key === 'ArrowUp' && options.length) {
      e.preventDefault()
      setActive((i) => (i <= 0 ? options.length - 1 : i - 1))
    }
  }

  const expanded = open && options.length > 0

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <form onSubmit={handleSubmit} className="flex" role="search">
        <input
          type="search"
          role="combobox"
          aria-expanded={expanded}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={expanded && active >= 0 ? `${listId}-${active}` : undefined}
          value={value}
          onChange={(e) => { setValue(e.target.value); setOpen(true); setActive(-1) }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={t('search.placeholder')}
          aria-label={t('search.ariaLabel')}
          className="flex-1 min-w-0 border border-gray-300 rounded-l-full pl-4 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
        />
        <button
          type="submit"
          className="bg-brand text-white px-5 rounded-r-full text-sm hover:bg-brand-dark"
        >
          {t('search.button')}
        </button>
      </form>

      {expanded && (
        <ul
          id={listId}
          role="listbox"
          aria-label={t('search.suggestions')}
          className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded shadow-lg z-50 overflow-hidden"
        >
          {options.map((o, i) => (
            <li
              key={o.key}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={i === active}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => {
                go(o.to)
                if (o.type !== 'all') setValue('')
              }}
              className={`flex items-center justify-between gap-3 px-3 py-2 text-sm cursor-pointer ${i === active ? 'bg-gray-100' : ''} ${o.type === 'all' ? 'border-t border-gray-100 text-brand' : ''}`}
            >
              <span>{o.label}</span>
              {o.type !== 'all' && <span className="text-xs text-gray-500">{o.hint}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
