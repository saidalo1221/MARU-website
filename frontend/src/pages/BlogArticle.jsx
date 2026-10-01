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
        <p className="text-gray-500 mb-4">{error}</p>
        <Link to="/blog" className="text-brand">{t('blog.backToBlog')}</Link>
      </div>
    )
  }

  if (!data) return <div className="max-w-3xl mx-auto px-4 py-6">{t('blog.loading')}</div>

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
    <div className="max-w-3xl mx-auto px-4 py-6">
      <Seo title={post.title} description={post.excerpt} image={post.cover_image_url} type="article" jsonLd={jsonLd} />
      <Link to="/blog" className="text-xs text-gray-500 mb-2 inline-block">{t('blog.backToBlog')}</Link>
      <p className="text-xs text-gray-500 mb-1">{post.category.name}</p>
      <h1 className="text-2xl font-bold mb-2">{post.title}</h1>
      {post.author_name && <p className="text-sm text-gray-500 mb-4">{t('blog.by', { name: post.author_name })}</p>}
      {post.cover_image_url && (
        <img src={post.cover_image_url} alt={post.title} className="w-full rounded-lg mb-6 object-cover max-h-96" />
      )}
      <div className="prose max-w-none whitespace-pre-wrap text-gray-800">{post.content}</div>

      {related.length > 0 && (
        <div className="mt-12">
          <h2 className="text-lg font-bold mb-4">{t('blog.related')}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {related.map((r) => (
              <Link key={r.id} to={`/blog/${r.slug}`} className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-sm transition-shadow">
                {r.cover_image_url && (
                  <img src={r.cover_image_url} alt={r.title} loading="lazy" decoding="async" className="w-full h-28 object-cover" />
                )}
                <div className="p-3">
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
