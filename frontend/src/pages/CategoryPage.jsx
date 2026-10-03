import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getCategory } from '../api/products'
import { useLocale } from '../context/LocaleContext'
import Catalog from './Catalog'
import NotFound from './NotFound'

// /shop/:slug - one category's page (PRD ТЗ№2 §10).
export default function CategoryPage() {
  const { slug } = useParams()
  const { locale } = useLocale()
  const [category, setCategory] = useState(null)
  const [missing, setMissing] = useState(false)

  useEffect(() => {
    setCategory(null)
    setMissing(false)
    getCategory(slug, locale).then(setCategory).catch(() => setMissing(true))
  }, [slug, locale])

  if (missing) return <NotFound />
  if (!category) return null
  return <Catalog key={category.id} category={category} />
}
