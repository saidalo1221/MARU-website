import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'
import { createReview, listReviews, uploadReviewImage } from '../../api/reviews'
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
  const [photos, setPhotos] = useState([])
  const [uploading, setUploading] = useState(false)

  const load = () => listReviews(slug).then(setSummary)

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug])

  const addPhoto = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || photos.length >= 3) return
    setError(null)
    setUploading(true)
    try {
      const url = await uploadReviewImage(file)
      setPhotos((p) => [...p, url])
    } catch (err) {
      setError(errorMessage(err, t('reviews.photoFailed')))
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await createReview(slug, { rating, content: content || null, image_urls: photos })
      setContent('')
      setPhotos([])
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
            {r.image_urls?.length > 0 && (
              <div className="flex gap-2 mt-2">
                {r.image_urls.map((u) => (
                  <a key={u} href={u} target="_blank" rel="noopener noreferrer"><img src={u} alt={t('reviews.photoAlt')} loading="lazy" className="h-16 w-16 object-cover rounded border border-gray-200" /></a>
                ))}
              </div>
            )}
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
          {photos.length > 0 && (
            <div className="flex gap-2">
              {photos.map((u) => (
                <div key={u} className="relative">
                  <img src={u} alt={t('reviews.photoAlt')} className="h-16 w-16 object-cover rounded border border-gray-200" />
                  <button type="button" aria-label={t('reviews.removePhoto')} onClick={() => setPhotos((p) => p.filter((x) => x !== u))} className="absolute -top-2 -right-2 bg-white border border-gray-300 rounded-full w-5 h-5 text-xs leading-none">×</button>
                </div>
              ))}
            </div>
          )}
          {photos.length < 3 && (
            <label className="block text-xs text-gray-500">{t('reviews.addPhotos')}
              <input type="file" accept="image/jpeg,image/png,image/webp" disabled={uploading} onChange={addPhoto} className="block mt-1 text-sm" />
            </label>
          )}
          {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={submitting || uploading} className="border border-brand text-brand rounded px-4 py-2 text-sm disabled:opacity-40">
            {submitting ? t('reviews.submitting') : t('reviews.submit')}
          </button>
        </form>
      )}
      {submitted && <p className="text-sm text-green-700 mt-3">{t('reviews.pendingModeration')}</p>}
    </div>
  )
}
