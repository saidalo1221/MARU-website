import { useEffect, useRef, useState } from 'react'
import { useLocale } from '../../context/LocaleContext'
import { classifyMedia, youtubeEmbed, youtubeThumb } from '../../lib/media'

// Big viewer + clickable thumbnail strip + prev/next arrows. `variant` is a
// ProductVariantOut: uses variant.images (the multi-item gallery) when
// present, falling back to the single legacy photo_url otherwise so older
// variants with no gallery rows still show their one photo. Each entry is a
// URL that may be an image, an mp4/webm video, or a YouTube link (see
// lib/media.js). Images zoom on hover (desktop) and open a full-screen
// lightbox on click.
export default function ProductGallery({ variant, alt }) {
  const { t } = useLocale()
  const urls = variant?.images?.length
    ? variant.images.map((img) => img.image_url)
    : variant?.photo_url
      ? [variant.photo_url]
      : []
  const items = urls.map(classifyMedia)

  const [index, setIndex] = useState(0)
  const [hoverZoom, setHoverZoom] = useState(null)
  const [lightboxOpen, setLightboxOpen] = useState(false)

  useEffect(() => {
    setIndex(0)
    setLightboxOpen(false)
  }, [variant?.id])

  if (items.length === 0) {
    return (
      <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
        <span className="text-gray-500">{t('product.noImage')}</span>
      </div>
    )
  }

  const current = items[Math.min(index, items.length - 1)]
  const prev = () => setIndex((i) => (i - 1 + items.length) % items.length)
  const next = () => setIndex((i) => (i + 1) % items.length)

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setHoverZoom({
      x: ((e.clientX - rect.left) / rect.width) * 100,
      y: ((e.clientY - rect.top) / rect.height) * 100,
    })
  }

  return (
    <div>
      <div className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
        {current.kind === 'image' && (
          <button
            type="button"
            onClick={() => setLightboxOpen(true)}
            onMouseMove={handleMouseMove}
            onMouseLeave={() => setHoverZoom(null)}
            aria-label={t('productDetail.zoomImage')}
            className="w-full h-full overflow-hidden cursor-zoom-in"
          >
            <img
              src={current.url}
              alt={alt}
              className="w-full h-full object-cover transition-transform duration-150"
              style={
                hoverZoom
                  ? { transform: 'scale(2)', transformOrigin: `${hoverZoom.x}% ${hoverZoom.y}%` }
                  : undefined
              }
            />
          </button>
        )}
        {current.kind === 'video' && (
          <video
            key={current.url}
            src={current.url}
            controls
            playsInline
            preload="metadata"
            className="w-full h-full object-contain bg-black"
          />
        )}
        {current.kind === 'youtube' && (
          <iframe
            key={current.youtubeId}
            src={youtubeEmbed(current.youtubeId)}
            title={t('productDetail.video')}
            allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="w-full h-full border-0"
          />
        )}

        {items.length > 1 && (
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

      {items.length > 1 && (
        <div className="flex gap-2 mt-2 overflow-x-auto pb-1">
          {items.map((item, i) => (
            <button
              key={item.url + i}
              type="button"
              onClick={() => setIndex(i)}
              aria-label={
                item.kind === 'image'
                  ? t('productDetail.thumbnail', { n: i + 1 })
                  : t('productDetail.videoThumbnail', { n: i + 1 })
              }
              className={`relative flex-shrink-0 w-16 h-16 rounded border-2 overflow-hidden bg-gray-900 ${
                i === index ? 'border-brand' : 'border-transparent'
              }`}
            >
              {item.kind === 'image' && <img src={item.url} alt="" className="w-full h-full object-cover" />}
              {item.kind === 'youtube' && (
                <img src={youtubeThumb(item.youtubeId)} alt="" className="w-full h-full object-cover" />
              )}
              {item.kind !== 'image' && (
                <span
                  aria-hidden="true"
                  className="absolute inset-0 flex items-center justify-center text-white text-lg bg-black/30"
                >
                  &#9654;
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {lightboxOpen && current.kind === 'image' && (
        <Lightbox
          items={items}
          startIndex={index}
          alt={alt}
          onIndexChange={setIndex}
          onClose={() => setLightboxOpen(false)}
        />
      )}
    </div>
  )
}

// Full-screen viewer that cycles through the image entries only (videos play
// inline in the gallery). Esc closes, arrow keys navigate, background click closes.
function Lightbox({ items, startIndex, alt, onIndexChange, onClose }) {
  const { t } = useLocale()
  const imageIndexes = items.map((it, i) => (it.kind === 'image' ? i : null)).filter((i) => i !== null)
  const [pos, setPos] = useState(Math.max(0, imageIndexes.indexOf(startIndex)))
  const closeRef = useRef(null)

  const go = (delta) => {
    const nextPos = (pos + delta + imageIndexes.length) % imageIndexes.length
    setPos(nextPos)
    onIndexChange(imageIndexes[nextPos])
  }

  useEffect(() => {
    closeRef.current?.focus()
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previousOverflow
    }
  }, [])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowLeft' && imageIndexes.length > 1) go(-1)
      else if (e.key === 'ArrowRight' && imageIndexes.length > 1) go(1)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  })

  return (
    <div
      className="fixed inset-0 z-[60] bg-black/90 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label={alt}
      onClick={onClose}
    >
      <button
        ref={closeRef}
        type="button"
        onClick={onClose}
        aria-label={t('product.quickViewClose')}
        className="absolute top-4 right-4 text-white text-3xl leading-none w-10 h-10 flex items-center justify-center"
      >
        &times;
      </button>
      <img
        src={items[imageIndexes[pos]].url}
        alt={alt}
        className="max-w-full max-h-full object-contain"
        onClick={(e) => e.stopPropagation()}
      />
      {imageIndexes.length > 1 && (
        <>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              go(-1)
            }}
            aria-label={t('productDetail.prevImage')}
            className="absolute left-3 top-1/2 -translate-y-1/2 bg-white/20 hover:bg-white/40 text-white rounded-full w-10 h-10 text-2xl leading-none"
          >
            &lsaquo;
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              go(1)
            }}
            aria-label={t('productDetail.nextImage')}
            className="absolute right-3 top-1/2 -translate-y-1/2 bg-white/20 hover:bg-white/40 text-white rounded-full w-10 h-10 text-2xl leading-none"
          >
            &rsaquo;
          </button>
        </>
      )}
    </div>
  )
}
