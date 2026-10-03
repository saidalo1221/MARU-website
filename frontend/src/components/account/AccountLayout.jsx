import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import AccountNav from './AccountNav'

// One frame for every /account page: the container and the tab bar stay mounted while only the page
// below changes, so switching tabs no longer re-creates the nav or jumps its width, and the reserved
// minimum height keeps the footer from bouncing while a page loads.
export default function AccountLayout() {
  const { user, loading } = useAuth()
  if (!loading && !user) return <Navigate to="/login" replace />

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:py-12">
      <AccountNav />
      <div className="min-h-[60vh]">{loading ? null : <Outlet />}</div>
    </div>
  )
}
