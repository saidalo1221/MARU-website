import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listBlogCategories, listBlogPosts } from '../api/blog'
import { useLocale } from '../context/LocaleContext'

export default function BlogHome() {
  const { locale, t } = useLocale()
  const [categories, setCategories] = useState([])
  const [posts, setPosts] = useState([])
  const [categoryFilter, setCategoryFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    listBlogCategories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    listBlogPosts(locale, categoryFilter || undefined)
      .then(setPosts)
      .catch(() => setError(t('blog.loadError')))
      .finally(() => setLoading(false))
  }, [locale, categoryFilter, t])

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <nav className="text-xs text-gray-500 mb-2">{t('blog.breadcrumb')}</nav>
      <h1 className="text-2xl font-bold mb-4">{t('blog.title')}</h1>

      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setCategoryFilter('')}
          className={`px-3 py-1.5 rounded text-sm border ${categoryFilter === '' ? 'bg-brand text-white border-brand' : 'border-gray-300'}`}
        >
          {t('blog.allCategories')}
        </button>
        {categories.map((c) => (
          <button
            key={c.id}
            onClick={() => setCategoryFilter(c.slug)}
            className={`px-3 py-1.5 rounded text-sm border ${categoryFilter === c.slug ? 'bg-brand text-white border-brand' : 'border-gray-300'}`}
          >
            {c.name}
          </button>
        ))}
      </div>

      {loading && <p>{t('blog.loading')}</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && posts.length === 0 && <p className="text-gray-500">{t('blog.noPosts')}</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {posts.map((p) => (
          <Link key={p.id} to={`/blog/${p.slug}`} className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-sm transition-shadow">
            {p.cover_image_url && (
              <img src={p.cover_image_url} alt={p.title} className="w-full h-40 object-cover" />
            )}
            <div className="p-4">
              <p className="text-xs text-gray-400 mb-1">{p.category.name}</p>
              <h2 className="font-semibold mb-1">{p.title}</h2>
              {p.excerpt && <p className="text-sm text-gray-500 line-clamp-2">{p.excerpt}</p>}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
