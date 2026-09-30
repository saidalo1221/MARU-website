import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'
import { createReview, listReviews } from '../../api/reviews'
import { errorMessage } from '../../api/client'

export default function Reviews({ slug }) {
  const { user } = useAuth()
  const { t } = useLocale()
  const [summary, setSummary] = useState(null)
  const [rating, setRating] = useState(5)
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  const load = () => listReviews(slug).then(setSummary)

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await createReview(slug, { rating, content: content || null })
      setContent('')
      setSubmitted(true)
      await load()
    } catch (err) {
      setError(errorMessage(err, t('reviews.submitFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  if (!summary) return null

  return (
    <div className="mt-6 border-t border-gray-200 pt-4">
      <p className="text-sm font-medium mb-2">
        {t('reviews.title')}
        {summary.count > 0 && ` (${summary.average_rating} ★ · ${summary.count})`}
      </p>

      {summary.reviews.length === 0 && <p className="text-sm text-gray-500">{t('reviews.none')}</p>}

      <ul className="space-y-3">
        {summary.reviews.map((r) => (
          <li key={r.id} className="text-sm border-b border-gray-100 pb-2">
            <p className="text-yellow-500">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</p>
            {r.content && <p className="text-gray-700 mt-1">{r.content}</p>}
          </li>
        ))}
      </ul>

      {user && !submitted && (
        <form onSubmit={handleSubmit} className="mt-4 space-y-2">
          <p className="text-sm font-medium">{t('reviews.leaveReview')}</p>
          <select aria-label={t('reviews.rating')} value={rating} onChange={(e) => setRating(Number(e.target.value))} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
            {[5, 4, 3, 2, 1].map((n) => (
              <option key={n} value={n}>{'★'.repeat(n)}{'☆'.repeat(5 - n)}</option>
            ))}
          </select>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={t('reviews.commentPlaceholder')}
            aria-label={t('reviews.commentPlaceholder')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            rows={3}
          />
          {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={submitting} className="border border-brand text-brand rounded px-4 py-2 text-sm disabled:opacity-40">
            {submitting ? t('reviews.submitting') : t('reviews.submit')}
          </button>
        </form>
      )}
      {submitted && <p className="text-sm text-green-700 mt-3">{t('reviews.pendingModeration')}</p>}
    </div>
  )
}
