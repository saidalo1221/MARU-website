import { Link } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'

// "By continuing you agree to the Terms and Privacy Policy" line for the
// places where a visitor commits (registering, placing an order).
export default function LegalNotice({ className = '' }) {
  const { t } = useLocale()
  return (
    <p className={`text-xs text-gray-500 ${className}`}>
      {t('legalNotice.before')}{' '}
      <Link to="/terms" className="underline">{t('footer.terms')}</Link>{' '}
      {t('legalNotice.and')}{' '}
      <Link to="/privacy" className="underline">{t('footer.privacy')}</Link>
      {t('legalNotice.after')}
    </p>
  )
}
