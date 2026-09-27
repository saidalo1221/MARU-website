import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'

export default function AdminDashboard() {
  const { user } = useAuth()
  const { t } = useLocale()

  const cards = [
    ['/admin/orders', t('admin.nav.orders'), t('admin.dashboard.orders')],
    ['/admin/quotes', t('admin.nav.quotes'), t('admin.dashboard.quotes')],
    ['/admin/reviews', t('admin.nav.reviews'), t('admin.dashboard.reviews')],
    ['/admin/blog/posts', t('admin.nav.blog'), t('admin.dashboard.blog')],
    ['/admin/site-settings', t('admin.nav.siteSettings'), t('admin.siteSettings.title')],
    ['/admin/products', t('admin.nav.products'), t('admin.dashboard.products')],
    ['/admin/categories', t('admin.nav.categories'), t('admin.dashboard.categories')],
    ['/admin/warehouses', t('admin.nav.warehouses'), t('admin.dashboard.warehouses')],
    ['/admin/promo-codes', t('admin.nav.promoCodes'), t('admin.dashboard.promoCodes')],
    ['/admin/shipping-rates', t('admin.nav.shippingRates'), t('admin.dashboard.shippingRates')],
    ['/admin/tax-rules', t('admin.nav.taxRules'), t('admin.dashboard.taxRules')],
    ['/admin/exchange-rates', t('admin.nav.exchangeRates'), t('admin.dashboard.exchangeRates')],
    ['/admin/notification-templates', t('admin.nav.notificationTemplates'), t('admin.dashboard.notificationTemplates')],
    ['/admin/integration-logs', t('admin.nav.integrationLogs'), t('admin.dashboard.integrationLogs')],
    ['/admin/audit-log', t('admin.nav.auditLog'), t('admin.dashboard.auditLog')],
    ['/admin/analytics-events', t('admin.nav.analyticsEvents'), t('admin.dashboard.analyticsEvents')],
    ['/admin/admins', t('admin.nav.admins'), t('admin.admins.subtitle')],
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{t('admin.nav.dashboard')}</h1>
      <p className="text-sm text-gray-500 mb-6">{t('admin.signedInAs', { email: user.email, role: user.role })}</p>
      <div className="grid sm:grid-cols-2 gap-4">
        {cards.map(([to, title, desc]) => (
          <Link key={to} to={to} className="border border-gray-200 rounded-lg p-4 hover:border-brand">
            <p className="font-semibold mb-1">{title}</p>
            <p className="text-sm text-gray-500">{desc}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
