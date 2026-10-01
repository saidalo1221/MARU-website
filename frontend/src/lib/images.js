// Uploaded images saved since the `img-` naming have WebP copies at 320/800/1600 px next to the
// original (app/routers/admin_uploads.py). Older uploads and external URLs have none, so they get no srcset.
const UPLOAD = /^(.*\/static\/uploads\/img-[0-9a-f]{32})\.(jpe?g|png|webp)$/i

export function imageSrcSet(url) {
  const m = typeof url === 'string' ? url.match(UPLOAD) : null
  if (!m) return undefined
  return [320, 800, 1600].map((w) => `${m[1]}-${w}.webp ${w}w`).join(', ')
}
