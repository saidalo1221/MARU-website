import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="max-w-md mx-auto px-4 py-16 text-center">
      <h1 className="text-2xl font-bold mb-2">Page not found</h1>
      <Link to="/" className="text-brand">Back to home</Link>
    </div>
  )
}
