// Uploaded images saved since the `img-` naming have AVIF + WebP copies at 320/800/1600 px next to the
// original (app/routers/admin_uploads.py). Older uploads and external URLs have none, so they get no srcset.
const UPLOAD = /^(.*\/static\/uploads\/img-[0-9a-f]{32})\.(jpe?g|png|webp)$/i
const WIDTHS = [320, 800, 1600]

function set(base, ext) {
  return WIDTHS.map((w) => `${base}-${w}.${ext} ${w}w`).join(', ')
}

// { avif, webp } srcset strings, or null when the image has no generated copies.
export function imageSources(url) {
  const m = typeof url === 'string' ? url.match(UPLOAD) : null
  return m ? { avif: set(m[1], 'avif'), webp: set(m[1], 'webp') } : null
}

export function imageSrcSet(url) {
  return imageSources(url)?.webp
}
