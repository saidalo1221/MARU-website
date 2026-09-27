import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useLocale } from '../context/LocaleContext'

export default function SearchBar({ className = '' }) {
  const { t } = useLocale()
  const [value, setValue] = useState('')
  const navigate = useNavigate()

  const handleSubmit = (e) => {
    e.preventDefault()
    navigate(`/search?q=${encodeURIComponent(value.trim())}`)
  }

  return (
    <form onSubmit={handleSubmit} className={`flex ${className}`} role="search">
      <input
        type="search"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={t('search.placeholder')}
        aria-label={t('search.ariaLabel')}
        className="flex-1 border border-gray-300 rounded-l px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
      />
      <button
        type="submit"
        className="bg-brand text-white px-4 rounded-r text-sm hover:bg-brand-dark"
      >
        {t('search.button')}
      </button>
    </form>
  )
}
