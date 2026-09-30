import { useEffect, useState } from 'react'
import { adminDemoteUser, adminListAdmins, adminPromoteUser } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'

const ROLES = ['super_admin', 'product_manager', 'sales_manager', 'warehouse_manager', 'accountant', 'marketing_manager']

export default function AdminAdmins() {
  const { t } = useLocale()
  const { user: currentUser } = useAuth()
  const [admins, setAdmins] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [email, setEmail] = useState('')
  const [role, setRole] = useState(ROLES[1])
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () =>
    adminListAdmins()
      .then(setAdmins)
      .catch((err) => setError(errorMessage(err, t('admin.admins.loadFailed'))))
      .finally(() => setLoading(false))

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleAdd = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      await adminPromoteUser(email, role)
      setEmail('')
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.admins.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDemote = async (id) => {
    try {
      await adminDemoteUser(id)
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.admins.saveFailed')))
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{t('admin.admins.title')}</h1>
      <p className="text-sm text-gray-500 mb-6">{t('admin.admins.subtitle')}</p>

      <form onSubmit={handleAdd} className="border border-gray-200 rounded-lg p-4 mb-6 flex flex-wrap gap-3 items-end">
        <div className="flex-1 min-w-[220px]">
          <label className="block text-xs text-gray-500 mb-1">{t('admin.admins.email')}</label>
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t('admin.admins.emailPlaceholder')} aria-label={t('admin.admins.emailPlaceholder')}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">{t('admin.admins.role')}</label>
          <select value={role} aria-label={t('admin.admins.role')} onChange={(e) => setRole(e.target.value)} className="border border-gray-300 rounded px-3 py-2 text-sm">
            {ROLES.map((r) => (
              <option key={r} value={r}>{t(`admin.admins.roles.${r}`)}</option>
            ))}
          </select>
        </div>
        <button type="submit" disabled={submitting} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
          {submitting ? t('admin.common.saving') : t('admin.admins.add')}
        </button>
      </form>
      {formError && <p role="alert" className="text-sm text-red-600 mb-4">{formError}</p>}

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2">{t('admin.admins.email')}</th>
                <th className="px-3 py-2">{t('admin.admins.role')}</th>
                <th className="px-3 py-2"><span className="sr-only">{t('admin.common.actions')}</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {admins.map((a) => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{a.email}</td>
                  <td className="px-3 py-2 text-gray-500">{t(`admin.admins.roles.${a.role}`)}</td>
                  <td className="px-3 py-2 text-right">
                    {a.id !== currentUser.id && (
                      <button onClick={() => handleDemote(a.id)} className="text-red-600">{t('admin.admins.revoke')}</button>
                    )}
                  </td>
                </tr>
              ))}
              {admins.length === 0 && <tr><td colSpan={3} className="px-3 py-6 text-center text-gray-500">{t('admin.admins.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
