import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'
import { listProducts } from '../api/products'
import { rankProducts } from '../lib/search'

const MAX_SUGGESTIONS = 5

export default function SearchBar({ className = '' }) {
  const { locale, t } = useLocale()
  const [value, setValue] = useState('')
  const [products, setProducts] = useState([])
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const containerRef = useRef(null)

  useEffect(() => {
    listProducts(locale).then(setProducts).catch(() => {})
  }, [locale])

  useEffect(() => {
    const onClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const suggestions = useMemo(
    () => (value.trim() ? rankProducts(products, value).slice(0, MAX_SUGGESTIONS) : []),
    [products, value]
  )

  const goToSearch = (query) => {
    setOpen(false)
    navigate(`/search?q=${encodeURIComponent(query.trim())}`)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    goToSearch(value)
  }

  const handleSelect = (product) => {
    setOpen(false)
    setValue('')
    navigate(`/products/${product.slug}`)
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <form onSubmit={handleSubmit} className="flex" role="search">
        <input
          type="search"
          value={value}
          onChange={(e) => { setValue(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          placeholder={t('search.placeholder')}
          aria-label={t('search.ariaLabel')}
          className="flex-1 min-w-0 border border-gray-300 rounded-l px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
        />
        <button
          type="submit"
          className="bg-brand text-white px-4 rounded-r text-sm hover:bg-brand-dark"
        >
          {t('search.button')}
        </button>
      </form>

      {open && suggestions.length > 0 && (
        <ul className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded shadow-lg z-50 overflow-hidden">
          {suggestions.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => handleSelect(p)}
                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
              >
                {p.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
