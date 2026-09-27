import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { getSiteSettings } from '../api/siteSettings'
import InquiryForm from '../components/forms/InquiryForm'
import MapPicker from '../components/MapPicker'

export default function Contact() {
  const { locale, t } = useLocale()
  const [settings, setSettings] = useState(null)

  useEffect(() => {
    getSiteSettings(locale).then(setSettings).catch(() => {})
  }, [locale])

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-3">{t('contact.title')}</h1>
      <p className="text-gray-600 mb-8">{t('contact.subtitle')}</p>

      <div className="grid md:grid-cols-2 gap-10">
        <div>
          <dl className="text-sm space-y-3 mb-8">
            <div>
              <dt className="text-gray-500">{t('contact.phone')}</dt>
              <dd className="font-medium">{settings?.phone || '—'}</dd>
            </div>
            <div>
              <dt className="text-gray-500">{t('contact.email')}</dt>
              <dd className="font-medium">{settings?.email || '—'}</dd>
            </div>
            <div>
              <dt className="text-gray-500">{t('contact.address')}</dt>
              <dd className="font-medium">{settings?.address || '—'}</dd>
            </div>
          </dl>
          {settings?.latitude != null && settings?.longitude != null ? (
            <div className="mb-6">
              <MapPicker latitude={settings.latitude} longitude={settings.longitude} readOnly />
            </div>
          ) : (
            <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center text-gray-400 text-sm mb-6">
              {t('contact.mapPlaceholder')}
            </div>
          )}
          <p className="text-xs text-gray-500">{t('contact.inquiriesNote')}</p>
        </div>

        <div className="border border-gray-200 rounded-lg p-6 h-fit">
          <h2 className="text-lg font-semibold mb-4">{t('contact.formTitle')}</h2>
          <InquiryForm defaultType="quote" lockType ctaKey="contact.send" />
        </div>
      </div>
    </div>
  )
}
