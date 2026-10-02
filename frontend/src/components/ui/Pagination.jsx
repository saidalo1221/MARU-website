import { useLocale } from '../../context/LocaleContext'

// Previous / next with "Page 2 of 5" (PRD §58 Pagination).
export default function Pagination({ page, pageCount, onChange }) {
  const { t } = useLocale()
  if (pageCount <= 1) return null
  return (
    <nav aria-label={t('catalog.pagination')} className="flex items-center justify-center gap-4 mt-10 text-sm">
      <button type="button" disabled={page <= 1} onClick={() => onChange(page - 1)} className="rounded-full border border-gray-300 px-5 py-2 transition-colors hover:bg-brand-light disabled:opacity-40 disabled:hover:bg-transparent">
        {t('catalog.prev')}
      </button>
      <span aria-current="page">{t('catalog.pageOf', { page, total: pageCount })}</span>
      <button type="button" disabled={page >= pageCount} onClick={() => onChange(page + 1)} className="rounded-full border border-gray-300 px-5 py-2 transition-colors hover:bg-brand-light disabled:opacity-40 disabled:hover:bg-transparent">
        {t('catalog.next')}
      </button>
    </nav>
  )
}
