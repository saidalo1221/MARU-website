import { Link } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'

export default function NotFound() {
  const { t } = useLocale()
  return (
    <div className="max-w-md mx-auto px-4 py-16 text-center">
      <h1 className="text-2xl font-bold mb-2">{t('notFound.title')}</h1>
      <Link to="/" className="text-brand">{t('notFound.backHome')}</Link>
    </div>
  )
}
