import { NavLink, Outlet } from 'react-router-dom'
import { useLocale } from '../../context/LocaleContext'
import { AdminCurrencyProvider } from '../../context/AdminCurrencyContext'
import AdminAccessGate from '../../components/admin/AdminAccessGate'
import Seo from '../../components/Seo'

const navLinkClass = ({ isActive }) =>
  `block px-3 py-1.5 rounded text-sm ${isActive ? 'bg-brand text-white' : 'text-gray-700 hover:bg-gray-100'}`

// Every admin action is still authorized server-side by require_role() on
// the specific endpoint (see app/dependencies.py) — this shell only decides
// whether to render the admin nav/pages at all. AdminAccessGate handles the
// /admin 2-step email login; a manager without permission for a given page
// still gets a 403 from the API, surfaced via errorMessage().
export default function AdminLayout() {
  const { t } = useLocale()

  const sections = [
    { title: null, links: [['/admin', t('admin.nav.dashboard')]] },
    {
      title: t('admin.sectionSales'),
      links: [
        ['/admin/orders', t('admin.nav.orders')],
        ['/admin/customers', t('admin.nav.customers')],
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
        ['/admin/stock', t('admin.nav.stock')],
        ['/admin/exchange-rates', t('admin.nav.exchangeRates')],
      ],
    },
    {
      title: t('admin.sectionMarketing'),
      links: [
        ['/admin/reviews', t('admin.nav.reviews')],
        ['/admin/loyalty', t('admin.nav.loyalty')],
        ['/admin/blog/posts', t('admin.nav.blog')],
        ['/admin/blog/categories', t('admin.blog.categoriesTitle')],
        ['/admin/site-settings', t('admin.nav.siteSettings')],
        ['/admin/about-sections', t('admin.nav.aboutSections')],
        ['/admin/page-sections', t('admin.nav.pageSections')],
        ['/admin/notification-templates', t('admin.nav.notificationTemplates')],
        ['/admin/analytics-events', t('admin.nav.analyticsEvents')],
        ['/admin/newsletter', t('admin.nav.newsletter')],
      ],
    },
    {
      title: t('admin.sectionSystem'),
      links: [
        ['/admin/integration-logs', t('admin.nav.integrationLogs')],
        ['/admin/webhooks', t('admin.nav.webhooks')],
        ['/admin/audit-log', t('admin.nav.auditLog')],
        ['/admin/admins', t('admin.nav.admins')],
      ],
    },
  ]

  return (
    <>
      <Seo title="Admin" noindex />
      <AdminAccessGate>
        <AdminCurrencyProvider>
        <div className="max-w-7xl mx-auto px-4 py-6 md:grid md:grid-cols-[210px_1fr] md:gap-8">
          <aside className="mb-6 md:mb-0 space-y-4">
            {sections.map((section, i) => (
              <div key={i}>
                {section.title && <p className="text-xs font-semibold text-gray-500 uppercase mb-1 px-3">{section.title}</p>}
                <nav aria-label={section.title || t('header.admin')} className="space-y-0.5">
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
      </AdminAccessGate>
    </>
  )
}
