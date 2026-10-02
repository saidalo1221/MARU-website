import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getBlogPost } from '../api/blog'
import { useLocale } from '../context/LocaleContext'
import Seo from '../components/Seo'

export default function BlogArticle() {
  const { slug } = useParams()
  const { locale, t } = useLocale()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setData(null)
    setError(null)
    getBlogPost(slug, locale)
      .then(setData)
      .catch(() => setError(t('blog.notFound')))
  }, [slug, locale, t])

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <p className="mb-4 text-gray-500">{error}</p>
        <Link to="/blog" className="text-brand underline">{t('blog.backToBlog')}</Link>
      </div>
    )
  }

  if (!data) return <div className="max-w-3xl mx-auto px-4 py-10 text-gray-500">{t('blog.loading')}</div>

  const { post, related } = data

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: post.title,
    description: post.excerpt || undefined,
    image: post.cover_image_url || undefined,
    author: post.author_name ? { '@type': 'Person', name: post.author_name } : undefined,
    datePublished: post.published_at || undefined,
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-10 md:py-14">
      <Seo title={post.title} description={post.excerpt} image={post.cover_image_url} type="article" jsonLd={jsonLd} />
      <Link to="/blog" className="mb-6 inline-block rounded-full border border-gray-300 px-4 py-1.5 text-sm transition-colors hover:bg-brand-light">{t('blog.backToBlog')}</Link>
      <p className="mb-3 inline-block rounded-full bg-brand-light px-3 py-0.5 text-xs font-medium text-brand">{post.category.name}</p>
      <h1 className="mb-3 text-3xl font-semibold tracking-tight md:text-5xl">{post.title}</h1>
      {post.author_name && <p className="mb-6 text-gray-500">{t('blog.by', { name: post.author_name })}</p>}
      {post.cover_image_url && (
        <img src={post.cover_image_url} alt={post.title} className="mb-8 max-h-[28rem] w-full rounded-3xl object-cover" />
      )}
      <div className="max-w-none whitespace-pre-wrap text-lg leading-relaxed text-gray-800">{post.content}</div>

      {related.length > 0 && (
        <div className="mt-16">
          <h2 className="mb-5 text-2xl font-semibold tracking-tight">{t('blog.related')}</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {related.map((r) => (
              <Link
                key={r.id}
                to={`/blog/${r.slug}`}
                className="overflow-hidden rounded-3xl border border-gray-200 bg-gray-50 transition duration-base hover:-translate-y-1 hover:shadow-token"
              >
                {r.cover_image_url && (
                  <div className="m-2 overflow-hidden rounded-2xl">
                    <img src={r.cover_image_url} alt={r.title} loading="lazy" decoding="async" className="h-28 w-full object-cover" />
                  </div>
                )}
                <div className="px-4 pb-4 pt-2">
                  <h3 className="text-sm font-semibold">{r.title}</h3>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
