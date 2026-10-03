import { imageSources } from '../../lib/images'

// <img> that offers AVIF and WebP copies (when the upload has them) and falls back to the original file.
// AVIF copies exist only for uploads made on a server whose Pillow can write AVIF; a browser that cannot
// decode a source type, or a missing AVIF file, falls through to the next <source> / the <img>.
export default function Picture({ src, sizes, alt, ...imgProps }) {
  const sources = imageSources(src)
  if (!sources) return <img src={src} alt={alt} {...imgProps} />
  return (
    <picture className="contents">
      <source type="image/avif" srcSet={sources.avif} sizes={sizes} />
      <source type="image/webp" srcSet={sources.webp} sizes={sizes} />
      <img src={src} alt={alt} {...imgProps} />
    </picture>
  )
}
