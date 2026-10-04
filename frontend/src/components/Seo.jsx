import { Helmet } from 'react-helmet-async'
import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { getSeoMeta } from '../api/siteContent'

const SITE_NAME = 'MARU'
const DEFAULT_DESCRIPTION =
  'Plastic food containers made in-house — polypropylene containers from 350 ml to 1900 ml, in stock and ready to ship.'

// Admin > SEO tags for every page of one language, fetched once per language.
const seoCache = {}
function useSeoOverrides(locale) {
  const [map, setMap] = useState(seoCache[locale]?.data || {})
  useEffect(() => {
    let active = true
    if (!seoCache[locale]) seoCache[locale] = { promise: getSeoMeta(locale).then((d) => (seoCache[locale].data = d || {})).catch(() => (seoCache[locale].data = {})) }
    seoCache[locale].promise.then((d) => active && setMap(d))
    return () => { active = false }
  }, [locale])
  return map
}

// Per-page <title>/meta description/canonical/Open Graph/Twitter Card tags,
// plus optional JSON-LD structured data. This is a client-rendered SPA (no
// SSR), so these tags land in the DOM after JS runs — search engines that
// execute JS (Google) see them fine, but link-preview bots that don't
// execute JS (many chat apps, some social platforms) will only ever see
// index.html's static fallback tags. True SSR/prerendering is the complete
// fix; this covers the common case cheaply.
export default function Seo({ title, description, image, type = 'website', path, jsonLd, noindex = false }) {
  const { locale } = useLocale()
  const custom = useSeoOverrides(locale)[path ?? (typeof window !== 'undefined' ? window.location.pathname : '')]
  if (custom?.image) image = custom.image
  if (custom?.noindex) noindex = true
  const fullTitle = custom?.title || (title ? `${title} | ${SITE_NAME}` : `${SITE_NAME} — Plastic Food Containers`)
  const desc = custom?.description || description || DEFAULT_DESCRIPTION
  const url = typeof window !== 'undefined' ? `${window.location.origin}${path ?? window.location.pathname}` : path

  return (
    // defer={false}: the default (deferred) commit schedules its DOM write
    // via requestAnimationFrame, which never fires in some automated/
    // headless browser contexts (and can lag a visible tab too) — commit
    // synchronously instead, since a handful of tags per navigation is not
    // a perf concern.
    <Helmet defer={false}>
      <html lang={locale} />
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
      {noindex && <meta name="robots" content="noindex, nofollow" />}
      {url && <link rel="canonical" href={url} />}

      <meta property="og:site_name" content={SITE_NAME} />
      <meta property="og:type" content={type} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={desc} />
      {url && <meta property="og:url" content={url} />}
      {image && <meta property="og:image" content={image} />}

      <meta name="twitter:card" content={image ? 'summary_large_image' : 'summary'} />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={desc} />
      {image && <meta name="twitter:image" content={image} />}

      {jsonLd && <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>}
    </Helmet>
  )
}
