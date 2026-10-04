import { useLocale } from '../context/LocaleContext'

// PRD section 53: dynamic components show a skeleton instead of a blank
// screen. The sr-only text keeps the loading state announced to screen
// readers; the pulsing blocks themselves are decorative.
export function ProductGridSkeleton({ count = 8 }) {
  const { t } = useLocale()
  return (
    <div role="status" aria-live="polite">
      <span className="sr-only">{t('common.loading')}</span>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4 md:gap-5 animate-pulse" aria-hidden="true">
        {Array.from({ length: count }, (_, i) => (
          <div key={i} className="overflow-hidden rounded-3xl border border-gray-200 bg-gray-50">
            <div className="m-2 aspect-square rounded-2xl bg-gray-200" />
            <div className="space-y-2 px-4 pb-4 pt-2">
              <div className="h-4 bg-gray-200 rounded w-3/4" />
              <div className="h-3 bg-gray-200 rounded w-1/3" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ProductDetailSkeleton() {
  const { t } = useLocale()
  return (
    <div className="max-w-5xl mx-auto px-4 py-6" role="status" aria-live="polite">
      <span className="sr-only">{t('common.loading')}</span>
      <div className="md:grid md:grid-cols-2 md:gap-8 animate-pulse" aria-hidden="true">
        <div>
          <div className="aspect-square bg-gray-200 rounded-3xl" />
          <div className="flex gap-2 mt-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className="w-20 h-20 bg-gray-200 rounded-2xl" />
            ))}
          </div>
        </div>
        <div className="mt-6 md:mt-0 space-y-4">
          <div className="h-7 bg-gray-200 rounded w-3/4" />
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="h-8 bg-gray-200 rounded w-1/2" />
          <div className="h-20 bg-gray-200 rounded" />
          <div className="h-11 bg-gray-200 rounded-full" />
        </div>
      </div>
    </div>
  )
}
