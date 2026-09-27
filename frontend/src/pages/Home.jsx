import { Link } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'

export default function Home() {
  const { t } = useLocale()
  return (
    <section className="max-w-3xl mx-auto text-center px-4 py-16">
      <h1 className="text-3xl md:text-4xl font-bold mb-4">
        {t('home.title')}
      </h1>
      <p className="text-gray-600 mb-8">
        {t('home.subtitle')}
      </p>
      <Link
        to="/shop"
        className="inline-block bg-brand text-white px-6 py-3 rounded font-medium hover:bg-brand-dark"
      >
        {t('home.cta')}
      </Link>
    </section>
  )
}
