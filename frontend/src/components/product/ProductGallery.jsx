import { useEffect, useState } from 'react'
import { useLocale } from '../../context/LocaleContext'

// Big image + clickable thumbnail strip + prev/next arrows. `variant` is a
// ProductVariantOut: uses variant.images (the new multi-photo gallery) when
// present, falling back to the single legacy photo_url otherwise so older
// variants with no gallery rows still show their one photo.
export default function ProductGallery({ variant, alt }) {
  const { t } = useLocale()
  const images = variant?.images?.length
    ? variant.images.map((img) => img.image_url)
    : variant?.photo_url
      ? [variant.photo_url]
      : []

  const [index, setIndex] = useState(0)

  useEffect(() => {
    setIndex(0)
  }, [variant?.id])

  if (images.length === 0) {
    return (
      <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
        <span className="text-gray-400">{t('product.noImage')}</span>
      </div>
    )
  }

  const prev = () => setIndex((i) => (i - 1 + images.length) % images.length)
  const next = () => setIndex((i) => (i + 1) % images.length)

  return (
    <div>
      <div className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
        <img src={images[index]} alt={alt} className="w-full h-full object-cover" />
        {images.length > 1 && (
          <>
            <button
              type="button"
              onClick={prev}
              aria-label={t('productDetail.prevImage')}
              className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full w-8 h-8 flex items-center justify-center text-lg leading-none shadow"
            >
              &lsaquo;
            </button>
            <button
              type="button"
              onClick={next}
              aria-label={t('productDetail.nextImage')}
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full w-8 h-8 flex items-center justify-center text-lg leading-none shadow"
            >
              &rsaquo;
            </button>
          </>
        )}
      </div>

      {images.length > 1 && (
        <div className="flex gap-2 mt-2 overflow-x-auto pb-1">
          {images.map((url, i) => (
            <button
              key={url + i}
              type="button"
              onClick={() => setIndex(i)}
              aria-label={t('productDetail.thumbnail', { n: i + 1 })}
              className={`flex-shrink-0 w-16 h-16 rounded border-2 overflow-hidden ${
                i === index ? 'border-brand' : 'border-transparent'
              }`}
            >
              <img src={url} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
