import { NavLink, Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const navLinkClass = ({ isActive }) =>
  `block px-3 py-1.5 rounded text-sm ${isActive ? 'bg-brand text-white' : 'text-gray-700 hover:bg-gray-100'}`

const SECTIONS = [
  { title: null, links: [['/admin', 'Dashboard']] },
  {
    title: 'Sales',
    links: [
      ['/admin/orders', 'Orders'],
      ['/admin/quotes', 'Quotes'],
      ['/admin/promo-codes', 'Promo Codes'],
      ['/admin/shipping-rates', 'Shipping Rates'],
      ['/admin/tax-rules', 'Tax Rules'],
    ],
  },
  {
    title: 'Catalog',
    links: [
      ['/admin/products', 'Products'],
      ['/admin/categories', 'Categories'],
      ['/admin/warehouses', 'Warehouses'],
      ['/admin/exchange-rates', 'Exchange Rates'],
    ],
  },
  {
    title: 'Marketing',
    links: [
      ['/admin/reviews', 'Reviews'],
      ['/admin/notification-templates', 'Notification Templates'],
      ['/admin/analytics-events', 'Analytics Events'],
    ],
  },
  {
    title: 'System',
    links: [
      ['/admin/integration-logs', 'Integration Logs'],
      ['/admin/audit-log', 'Audit Log'],
    ],
  },
]

// Every admin action is still authorized server-side by require_role() on
// the specific endpoint (see app/dependencies.py) — this gate only decides
// whether to show the admin shell at all. A manager without permission for
// a given page will get a 403 from the API, surfaced via errorMessage().
export default function AdminLayout() {
  const { user, loading } = useAuth()

  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'customer') {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center">
        <h1 className="text-xl font-bold mb-2">Access denied</h1>
        <p className="text-sm text-gray-500">Your account doesn't have admin access.</p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 md:grid md:grid-cols-[210px_1fr] md:gap-8">
      <aside className="mb-6 md:mb-0 space-y-4">
        {SECTIONS.map((section, i) => (
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
  )
}
