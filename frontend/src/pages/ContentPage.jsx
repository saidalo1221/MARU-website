import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listPageSections } from '../api/pageSections'
import { useLocale } from '../context/LocaleContext'
import InfoSections from '../components/layout/InfoSections'
import PageIntro from '../components/layout/PageIntro'
import Seo from '../components/Seo'

// A page whose body is made of admin-editable sections (Admin > Support Pages
// Content), e.g. Manufacturing and Quality (PRD ТЗ№2 §34). Nothing is shown
// that an admin hasn't entered, so no unverified claims appear by default.
export default function ContentPage({ pageKey }) {
  const { t, locale } = useLocale()
  const [sections, setSections] = useState([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    listPageSections(pageKey, locale)
      .then(setSections)
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [pageKey, locale])

  const title = t(`contentPages.${pageKey}Title`)
  return (
    <div className="max-w-4xl mx-auto px-4 py-12 md:py-16">
      <Seo title={title} />
      <PageIntro title={title} subtitle={t(`contentPages.${pageKey}Subtitle`)} />

      <InfoSections sections={sections} className="mb-10" />
      {loaded && sections.length === 0 && (
        <p className="mb-10 rounded-3xl bg-brand-light px-6 py-10 text-center text-gray-700">{t('contentPages.empty')}</p>
      )}

      <div className="flex flex-wrap justify-center gap-3">
        <Link to="/about" className="rounded-full border border-brand px-6 py-2.5 text-sm font-semibold text-brand transition-colors hover:bg-brand-light">{t('header.company')}</Link>
        <Link to="/contact" className="rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-dark">{t('footer.contact')}</Link>
      </div>
    </div>
  )
}
