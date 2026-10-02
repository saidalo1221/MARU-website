import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'
import { getSiteSettings } from '../api/siteSettings'
import { listPageSections } from '../api/pageSections'
import InquiryForm from '../components/forms/InquiryForm'
import PageIntro from '../components/layout/PageIntro'
import MapPicker from '../components/MapPicker'
import Seo from '../components/Seo'

export default function Contact() {
  const { locale, t } = useLocale()
  const [settings, setSettings] = useState(null)
  const [sections, setSections] = useState([])

  useEffect(() => {
    getSiteSettings(locale).then(setSettings).catch(() => {})
  }, [locale])

  useEffect(() => {
    listPageSections('contact', locale).then(setSections).catch(() => {})
  }, [locale])

  const details = [
    ['contact.phone', settings?.phone],
    ['contact.email', settings?.email],
    ['contact.address', settings?.address],
  ]

  return (
    <div className="max-w-5xl mx-auto px-4 py-12 md:py-16">
      <Seo title={t('contact.title')} />
      <PageIntro title={t('contact.title')} subtitle={t('contact.subtitle')} />

      <div className="grid gap-8 md:grid-cols-2">
        <div>
          <dl className="mb-6 space-y-3">
            {details.map(([key, value]) => (
              <div key={key} className="rounded-2xl border border-gray-200 bg-gray-50 px-6 py-4">
                <dt className="text-sm text-gray-500">{t(key)}</dt>
                <dd className="font-semibold">{value || '-'}</dd>
              </div>
            ))}
          </dl>
          {settings?.latitude != null && settings?.longitude != null ? (
            <div className="mb-6 overflow-hidden rounded-3xl">
              <MapPicker latitude={settings.latitude} longitude={settings.longitude} readOnly />
            </div>
          ) : (
            <div className="mb-6 flex aspect-video items-center justify-center rounded-3xl bg-brand-light text-sm text-gray-500">
              {t('contact.mapPlaceholder')}
            </div>
          )}
          {sections.map((s) => (
            <div key={s.id} className="mb-3">
              <p className="text-sm font-medium text-gray-700">{s.title}</p>
              <p className="text-sm text-gray-500">{s.body}</p>
            </div>
          ))}
        </div>

        <div className="h-fit rounded-3xl border border-gray-200 bg-gray-50 p-6 md:p-8">
          <h2 className="mb-5 text-xl font-semibold">{t('contact.formTitle')}</h2>
          <InquiryForm defaultType="quote" lockType ctaKey="contact.send" />
          <ul className="mt-5 space-y-1 text-sm">
            <li><Link to="/b2b" className="text-brand underline">{t('contact.businessInquiries')}</Link></li>
            <li><Link to="/wholesale" className="text-brand underline">{t('contact.wholesaleInquiries')}</Link></li>
          </ul>
        </div>
      </div>
    </div>
  )
}
