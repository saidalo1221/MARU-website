import { Link } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'

// Crawlable breadcrumb trail (PRD ТЗ№2 §62). `items` are the links before the
// current page: [{ to, label }]; `current` is the label of the page itself.
export default function Breadcrumbs({ items, current, className = 'mb-4' }) {
  const { t } = useLocale()
  return (
    <nav aria-label={t('common.breadcrumb')} className={`text-xs text-gray-500 ${className}`}>
      <ol className="flex flex-wrap items-center gap-1">
        {items.map((item) => (
          <li key={item.to} className="flex items-center gap-1">
            <Link to={item.to} className="hover:underline">{item.label}</Link>
            <span aria-hidden="true">/</span>
          </li>
        ))}
        <li aria-current="page">{current}</li>
      </ol>
    </nav>
  )
}
