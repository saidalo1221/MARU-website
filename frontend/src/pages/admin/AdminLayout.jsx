import { NavLink, Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'
import { AdminCurrencyProvider } from '../../context/AdminCurrencyContext'

const navLinkClass = ({ isActive }) =>
  `block px-3 py-1.5 rounded text-sm ${isActive ? 'bg-brand text-white' : 'text-gray-700 hover:bg-gray-100'}`

// Every admin action is still authorized server-side by require_role() on
// the specific endpoint (see app/dependencies.py) — this gate only decides
// whether to show the admin shell at all. A manager without permission for
// a given page will get a 403 from the API, surfaced via errorMessage().
export default function AdminLayout() {
  const { user, loading } = useAuth()
  const { t } = useLocale()

  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'customer') {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center">
        <h1 className="text-xl font-bold mb-2">{t('admin.accessDeniedTitle')}</h1>
        <p className="text-sm text-gray-500">{t('admin.accessDeniedText')}</p>
      </div>
    )
  }

  const sections = [
    { title: null, links: [['/admin', t('admin.nav.dashboard')]] },
    {
      title: t('admin.sectionSales'),
      links: [
        ['/admin/orders', t('admin.nav.orders')],
        ['/admin/quotes', t('admin.nav.quotes')],
        ['/admin/promo-codes', t('admin.nav.promoCodes')],
        ['/admin/shipping-rates', t('admin.nav.shippingRates')],
        ['/admin/tax-rules', t('admin.nav.taxRules')],
      ],
    },
    {
      title: t('admin.sectionCatalog'),
      links: [
        ['/admin/products', t('admin.nav.products')],
        ['/admin/categories', t('admin.nav.categories')],
        ['/admin/warehouses', t('admin.nav.warehouses')],
        ['/admin/exchange-rates', t('admin.nav.exchangeRates')],
      ],
    },
    {
      title: t('admin.sectionMarketing'),
      links: [
        ['/admin/reviews', t('admin.nav.reviews')],
        ['/admin/blog/posts', t('admin.nav.blog')],
        ['/admin/blog/categories', t('admin.blog.categoriesTitle')],
        ['/admin/notification-templates', t('admin.nav.notificationTemplates')],
        ['/admin/analytics-events', t('admin.nav.analyticsEvents')],
      ],
    },
    {
      title: t('admin.sectionSystem'),
      links: [
        ['/admin/integration-logs', t('admin.nav.integrationLogs')],
        ['/admin/audit-log', t('admin.nav.auditLog')],
      ],
    },
  ]

  return (
    <AdminCurrencyProvider>
      <div className="max-w-7xl mx-auto px-4 py-6 md:grid md:grid-cols-[210px_1fr] md:gap-8">
        <aside className="mb-6 md:mb-0 space-y-4">
          {sections.map((section, i) => (
            <div key={i}>
              {section.title && <p className="text-xs font-semibold text-gray-400 uppercase mb-1 px-3">{section.title}</p>}
              <nav className="space-y-0.5">
                {section.links.map(([to, label]) => (
                  <NavLink key={to} to={to} end={to === '/admin'} className={navLinkClass}>
                    {label}
                  </NavLink>
                ))}
              </nav>
            </div>
          ))}
        </aside>
        <div>
          <Outlet />
        </div>
      </div>
    </AdminCurrencyProvider>
  )
}
