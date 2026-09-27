import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../api/client'

const emptyForm = { email: '', password: '', first_name: '', last_name: '', phone: '' }

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await register(form)
      navigate('/account/orders')
    } catch (err) {
      setError(err instanceof ApiError ? (err.detail || 'Registration failed') : 'Registration failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold mb-6">Create an account</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input required placeholder="First name" value={form.first_name} onChange={update('first_name')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <input required placeholder="Last name" value={form.last_name} onChange={update('last_name')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <input placeholder="Phone" value={form.phone} onChange={update('phone')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <input required type="email" placeholder="Email" value={form.email} onChange={update('email')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <input required type="password" placeholder="Password" value={form.password} onChange={update('password')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className="w-full bg-brand text-white rounded py-2.5 font-medium disabled:opacity-40">
          {submitting ? 'Creating account...' : 'Create Account'}
        </button>
      </form>
      <p className="text-sm text-gray-500 mt-4">
        Already have an account? <Link to="/login" className="text-brand">Login</Link>
      </p>
    </div>
  )
}
