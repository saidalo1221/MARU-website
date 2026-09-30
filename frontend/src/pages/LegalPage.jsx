import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { getSiteSettings } from '../api/siteSettings'
import { listPageSections } from '../api/pageSections'
import { LEGAL } from '../i18n/legal'
import Seo from '../components/Seo'

// Shared by /privacy and /terms. Admin-written sections (Support Pages
// Content) replace the built-in default text as soon as at least one exists.
export default function LegalPage({ pageKey }) {
  const { locale } = useLocale()
  const copy = (LEGAL[locale] || LEGAL.en)
  const doc = copy[pageKey]
  const [adminSections, setAdminSections] = useState(null)
  const [settings, setSettings] = useState(null)

  useEffect(() => {
    setAdminSections(null)
    listPageSections(pageKey, locale).then(setAdminSections).catch(() => setAdminSections([]))
  }, [pageKey, locale])

  useEffect(() => {
    getSiteSettings(locale).then(setSettings).catch(() => {})
  }, [locale])

  const custom = adminSections && adminSections.length > 0
  const sections = custom ? adminSections.map((s) => ({ title: s.title, body: s.body })) : doc.sections

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Seo title={doc.title} />
      <h1 className="text-3xl font-bold mb-2">{doc.title}</h1>
      {!custom && (
        <>
          <p className="text-xs text-gray-500 mb-4">{copy.updated}</p>
          <p className="text-gray-600 mb-8">{doc.intro}</p>
        </>
      )}

      <div className="space-y-6">
        {sections.map((s, i) => (
          <section key={i}>
            <h2 className="font-semibold mb-1">{s.title}</h2>
            <p className="text-sm text-gray-600 whitespace-pre-line">{s.body}</p>
          </section>
        ))}
      </div>

      {settings && (settings.email || settings.phone || settings.address) && (
        <section className="mt-10 border-t border-gray-200 pt-6">
          <h2 className="font-semibold mb-2">{copy.contactTitle}</h2>
          <address className="text-sm text-gray-600 not-italic space-y-1">
            {settings.address && <p>{settings.address}</p>}
            {settings.email && <p><a href={`mailto:${settings.email}`} className="underline">{settings.email}</a></p>}
            {settings.phone && <p>{settings.phone}</p>}
          </address>
        </section>
      )}
    </div>
  )
}
