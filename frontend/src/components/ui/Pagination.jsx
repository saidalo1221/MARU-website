import { useLocale } from '../../context/LocaleContext'

// Previous / next with "Page 2 of 5" (PRD §58 Pagination).
export default function Pagination({ page, pageCount, onChange }) {
  const { t } = useLocale()
  if (pageCount <= 1) return null
  return (
    <nav aria-label={t('catalog.pagination')} className="flex items-center justify-center gap-3 mt-6 text-sm">
      <button type="button" disabled={page <= 1} onClick={() => onChange(page - 1)} className="border border-gray-300 rounded px-3 py-1.5 disabled:opacity-40">
        {t('catalog.prev')}
      </button>
      <span aria-current="page">{t('catalog.pageOf', { page, total: pageCount })}</span>
      <button type="button" disabled={page >= pageCount} onClick={() => onChange(page + 1)} className="border border-gray-300 rounded px-3 py-1.5 disabled:opacity-40">
        {t('catalog.next')}
      </button>
    </nav>
  )
}
