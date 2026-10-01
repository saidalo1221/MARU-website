import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { adminAddMarketingSpend, adminDashboard, adminDeleteMarketingSpend, adminListMarketingSpend } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'

const usd = (n) => (n == null ? null : `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`)
const pct = (n) => (n == null ? null : `${(n * 100).toFixed(n < 0.1 ? 2 : 1)}%`)

function Stat({ label, value, hint }) {
  const { t } = useLocale()
  return (
    <div className="border border-gray-200 rounded-lg p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-xl font-semibold mt-1">{value ?? <span className="text-gray-400 text-base">{t('admin.dashboard.noData')}</span>}</p>
      {hint && <p className="text-xs text-gray-500 mt-1">{hint}</p>}
    </div>
  )
}

function Section({ title, children, note }) {
  return (
    <section className="mb-6">
      <h2 className="font-semibold mb-2">{title}</h2>
      {children}
      {note && <p className="text-xs text-gray-500 mt-2">{note}</p>}
    </section>
  )
}

function SpendPanel({ onChanged }) {
  const { t } = useLocale()
  const [rows, setRows] = useState([])
  const [form, setForm] = useState({ month: new Date().toISOString().slice(0, 10), channel: '', amount_usd: '' })
  const [error, setError] = useState(null)

  const load = () => adminListMarketingSpend().then(setRows).catch(() => setRows([]))
  useEffect(() => { load() }, [])

  const add = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      await adminAddMarketingSpend({ month: form.month, channel: form.channel, amount_usd: Number(form.amount_usd) })
      setForm((f) => ({ ...f, channel: '', amount_usd: '' }))
      await load()
      onChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.dashboard.spendFailed')))
    }
  }
  const remove = async (id) => {
    await adminDeleteMarketingSpend(id)
    await load()
    onChanged()
  }

  return (
    <div className="mt-3">
      <form onSubmit={add} className="flex flex-wrap gap-2 items-end">
        <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.dashboard.spendMonth')}
          <input type="date" required value={form.month} onChange={(e) => setForm((f) => ({ ...f, month: e.target.value }))} className="border border-gray-300 rounded px-2 py-1.5 text-sm text-gray-900" />
        </label>
        <input required maxLength={60} placeholder={t('admin.dashboard.spendChannel')} aria-label={t('admin.dashboard.spendChannel')} value={form.channel} onChange={(e) => setForm((f) => ({ ...f, channel: e.target.value }))} className="border border-gray-300 rounded px-2 py-1.5 text-sm" />
        <input required type="number" min="0.01" step="0.01" placeholder={t('admin.dashboard.spendAmount')} aria-label={t('admin.dashboard.spendAmount')} value={form.amount_usd} onChange={(e) => setForm((f) => ({ ...f, amount_usd: e.target.value }))} className="border border-gray-300 rounded px-2 py-1.5 text-sm w-32" />
        <button type="submit" className="bg-brand text-white rounded px-3 py-1.5 text-sm">{t('admin.dashboard.addSpend')}</button>
      </form>
      {error && <p role="alert" className="text-sm text-red-600 mt-1">{error}</p>}
      {rows.length > 0 && (
        <ul className="mt-2 text-sm divide-y divide-gray-100 border border-gray-200 rounded">
          {rows.slice(0, 6).map((r) => (
            <li key={r.id} className="flex justify-between px-3 py-1.5">
              <span>{r.month.slice(0, 7)} · {r.channel} · {usd(r.amount_usd)}</span>
              <button type="button" onClick={() => remove(r.id)} className="text-red-600">{t('admin.dashboard.delete')}</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function AdminDashboard() {
  const { user } = useAuth()
  const { t } = useLocale()
  const [data, setData] = useState(null)
  const [noStats, setNoStats] = useState(false)

  const load = () => adminDashboard().then(setData).catch(() => setNoStats(true))
  useEffect(() => { load() }, [])

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

  const d = data
  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{t('admin.nav.dashboard')}</h1>
      <p className="text-sm text-gray-500 mb-6">{t('admin.signedInAs', { email: user?.email, role: user?.role })}</p>

      {d && !noStats && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-1">{t('admin.dashboard.statsTitle')}</h2>
          <p className="text-xs text-gray-500 mb-4">{t('admin.dashboard.usdNote')}</p>

          <Section title={t('admin.dashboard.today')}>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <Stat label={t('admin.dashboard.statOrders')} value={d.today.orders} />
              <Stat label={t('admin.dashboard.revenue')} value={usd(d.today.revenue)} />
              <Stat label={t('admin.dashboard.units')} value={d.today.units} />
              <Stat label={t('admin.dashboard.aov')} value={usd(d.today.average_order_value)} />
            </div>
          </Section>

          <Section title={t('admin.dashboard.month')}>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <Stat label={t('admin.dashboard.revenue')} value={usd(d.month.revenue)} />
              <Stat label={t('admin.dashboard.grossProfit')} value={usd(d.month.gross_profit)} hint={d.month.cost_coverage != null ? t('admin.dashboard.costCoverage', { pct: Math.round(d.month.cost_coverage * 100) }) : null} />
              <Stat label={t('admin.dashboard.grossMargin')} value={pct(d.month.gross_margin)} />
              <Stat label={t('admin.dashboard.statOrders')} value={d.month.orders} />
              <Stat label={t('admin.dashboard.customers')} value={d.month.customers} />
              <Stat label={t('admin.dashboard.visitors')} value={d.month.visitors} />
              <Stat label={t('admin.dashboard.conversion')} value={pct(d.month.conversion_rate)} />
            </div>
          </Section>

          <Section title={t('admin.dashboard.markets')}>
            <div className="grid sm:grid-cols-3 gap-3">
              {d.markets.map((m) => (
                <Stat key={m.market} label={t(`admin.dashboard.market${m.market}`)} value={usd(m.revenue)} hint={`${m.orders} ${t('admin.dashboard.statOrders').toLowerCase()}`} />
              ))}
            </div>
          </Section>

          <Section title={t('admin.dashboard.customerStats')}>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              <Stat label={t('admin.dashboard.newCustomers')} value={d.customers.new_this_month} />
              <Stat label={t('admin.dashboard.returningCustomers')} value={d.customers.returning_this_month} />
              <Stat label={t('admin.dashboard.repeatRate')} value={pct(d.customers.repeat_purchase_rate)} />
              <Stat label={t('admin.dashboard.ltv')} value={usd(d.customers.lifetime_value)} />
              <Stat label={t('admin.dashboard.frequency')} value={d.customers.orders_per_customer} />
            </div>
          </Section>

          <Section title={t('admin.dashboard.marketing')} note={t('admin.dashboard.spendHint')}>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <Stat label={t('admin.dashboard.spend')} value={usd(d.marketing.spend)} />
              <Stat label={t('admin.dashboard.cac')} value={usd(d.marketing.cac)} />
              <Stat label={t('admin.dashboard.roas')} value={d.marketing.roas != null ? `${d.marketing.roas}×` : null} />
            </div>
            <SpendPanel onChanged={load} />
          </Section>

          <Section title={t('admin.dashboard.funnel')} note={t('admin.dashboard.funnelHint')}>
            <ol className="space-y-1">
              {d.funnel.map((f) => (
                <li key={f.stage} className="flex items-center gap-3 text-sm">
                  <span className="w-40 shrink-0">{t(`admin.dashboard.stage_${f.stage}`)}</span>
                  <span className="w-12 text-right font-medium">{f.count}</span>
                  <span className="w-14 text-gray-500">{pct(f.rate_from_previous) ?? ''}</span>
                </li>
              ))}
            </ol>
          </Section>

          {d.sources.length > 0 && (
            <Section title={t('admin.dashboard.sources')}>
              <table className="w-full text-sm border border-gray-200 rounded">
                <thead className="bg-gray-50 text-left">
                  <tr>
                    <th scope="col" className="px-3 py-1.5">{t('admin.dashboard.source')}</th>
                    <th scope="col" className="px-3 py-1.5">{t('admin.dashboard.statOrders')}</th>
                    <th scope="col" className="px-3 py-1.5">{t('admin.dashboard.revenue')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {d.sources.map((s) => (
                    <tr key={s.source}><td className="px-3 py-1.5">{s.source}</td><td className="px-3 py-1.5">{s.orders}</td><td className="px-3 py-1.5">{usd(s.revenue)}</td></tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}
        </div>
      )}

      <h2 className="text-lg font-semibold mb-3">{t('admin.dashboard.quickLinks')}</h2>
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
