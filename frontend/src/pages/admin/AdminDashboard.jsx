import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export default function AdminDashboard() {
  const { user } = useAuth()
  const cards = [
    ['/admin/orders', 'Orders', 'View and update order status, process refunds.'],
    ['/admin/quotes', 'Quotes', 'Review RFQs, set pricing, convert to orders.'],
    ['/admin/reviews', 'Reviews', 'Approve or reject pending customer reviews.'],
    ['/admin/products', 'Products', 'Edit product listings.'],
    ['/admin/categories', 'Categories', 'Manage the category tree.'],
    ['/admin/warehouses', 'Warehouses', 'Manage warehouse locations and priority.'],
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Dashboard</h1>
      <p className="text-sm text-gray-500 mb-6">Signed in as {user.email} ({user.role})</p>
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
