import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listBlogCategories, listBlogPosts } from '../api/blog'
import { useLocale } from '../context/LocaleContext'
import Breadcrumbs from '../components/Breadcrumbs'
import PageIntro from '../components/layout/PageIntro'
import Seo from '../components/Seo'

const chip = (active) =>
  `rounded-full border px-5 py-2 text-sm font-medium transition-colors ${
    active ? 'border-brand bg-brand text-white' : 'border-gray-300 hover:bg-brand-light'
  }`

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
    <div className="max-w-7xl mx-auto px-4 py-8 md:py-12">
      <Seo title={t('blog.title')} />
      <Breadcrumbs items={[{ to: '/', label: t('header.home') }]} current={t('footer.blog')} className="mb-6" />
      <PageIntro title={t('blog.title')} className="!mb-8" />

      <div className="mb-10 flex flex-wrap justify-center gap-2">
        <button onClick={() => setCategoryFilter('')} className={chip(categoryFilter === '')}>
          {t('blog.allCategories')}
        </button>
        {categories.map((c) => (
          <button key={c.id} onClick={() => setCategoryFilter(c.slug)} className={chip(categoryFilter === c.slug)}>
            {c.name}
          </button>
        ))}
      </div>

      {loading && <p className="text-center text-gray-500">{t('blog.loading')}</p>}
      {error && <p role="alert" className="text-center text-red-600">{error}</p>}
      {!loading && !error && posts.length === 0 && (
        <p className="rounded-3xl bg-brand-light px-6 py-14 text-center text-gray-700">{t('blog.noPosts')}</p>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {posts.map((p) => (
          <Link
            key={p.id}
            to={`/blog/${p.slug}`}
            className="group overflow-hidden rounded-3xl border border-gray-200 bg-gray-50 transition duration-base hover:-translate-y-1 hover:shadow-token"
          >
            {p.cover_image_url && (
              <div className="m-2 overflow-hidden rounded-2xl">
                <img src={p.cover_image_url} alt={p.title} loading="lazy" decoding="async" className="h-48 w-full object-cover" />
              </div>
            )}
            <div className="px-5 pb-5 pt-3">
              <p className="mb-2 inline-block rounded-full bg-brand-light px-3 py-0.5 text-xs font-medium text-brand">{p.category.name}</p>
              <h2 className="mb-1 text-lg font-semibold">{p.title}</h2>
              {p.excerpt && <p className="line-clamp-2 text-sm text-gray-600">{p.excerpt}</p>}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
