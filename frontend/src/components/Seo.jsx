import { Helmet } from 'react-helmet-async'
import { useLocale } from '../context/LocaleContext'

const SITE_NAME = 'MARU'
const DEFAULT_DESCRIPTION =
  'Plastic food containers made in-house — polypropylene containers from 350 ml to 1900 ml, in stock and ready to ship.'

// Per-page <title>/meta description/canonical/Open Graph/Twitter Card tags,
// plus optional JSON-LD structured data. This is a client-rendered SPA (no
// SSR), so these tags land in the DOM after JS runs — search engines that
// execute JS (Google) see them fine, but link-preview bots that don't
// execute JS (many chat apps, some social platforms) will only ever see
// index.html's static fallback tags. True SSR/prerendering is the complete
// fix; this covers the common case cheaply.
export default function Seo({ title, description, image, type = 'website', path, jsonLd, noindex = false }) {
  const { locale } = useLocale()
  const fullTitle = title ? `${title} | ${SITE_NAME}` : `${SITE_NAME} — Plastic Food Containers`
  const desc = description || DEFAULT_DESCRIPTION
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
