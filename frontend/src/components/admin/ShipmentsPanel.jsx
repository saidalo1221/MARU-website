import { useState } from 'react'
import { adminAddShipmentEvent, adminCreateShipment } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import { formatDateTime } from '../../lib/format'

const NEXT_STATUSES = {
  shipped: ['in_transit', 'delivered', 'returned'],
  in_transit: ['in_transit', 'delivered', 'returned'],
  delivered: ['returned'],
  returned: [],
}

function ShipmentCard({ orderId, shipment, onChanged }) {
  const { t } = useLocale()
  const options = NEXT_STATUSES[shipment.status] || []
  const [status, setStatus] = useState(options[0] || '')
  const [location, setLocation] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await adminAddShipmentEvent(orderId, shipment.id, { status, location: location || null })
      setLocation('')
      await onChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.orderDetail.eventFailed')))
    } finally {
      setBusy(false)
    }
  }

  return (
    <li className="border border-gray-200 rounded p-3 text-sm">
      <div className="flex justify-between">
        <span className="font-medium">{shipment.carrier}{shipment.tracking_number ? ` · ${shipment.tracking_number}` : ''}</span>
        <span>{t(`orderStatus.shipmentStatus.${shipment.status}`)}</span>
      </div>
      <ol className="mt-2 text-xs text-gray-500 space-y-0.5">
        {shipment.events.map((ev, i) => (
          <li key={i}>
            {t(`orderStatus.shipmentStatus.${ev.status}`)}{ev.location ? ` · ${ev.location}` : ''} · {formatDateTime(ev.occurred_at)}
          </li>
        ))}
      </ol>
      {options.length > 0 && (
        <form onSubmit={submit} className="mt-3 flex flex-wrap gap-2 items-start">
          <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label={t('admin.orderDetail.eventStatus')} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
            {options.map((s) => <option key={s} value={s}>{t(`orderStatus.shipmentStatus.${s}`)}</option>)}
          </select>
          <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder={t('admin.orderDetail.location')} aria-label={t('admin.orderDetail.location')} className="flex-1 min-w-[8rem] border border-gray-300 rounded px-2 py-1.5 text-sm" />
          <button type="submit" disabled={busy} className="border border-gray-300 rounded px-3 py-1.5 text-sm disabled:opacity-40">{t('admin.orderDetail.addEvent')}</button>
          {error && <p role="alert" className="w-full text-sm text-red-600">{error}</p>}
        </form>
      )}
    </li>
  )
}

export default function ShipmentsPanel({ order, onChanged }) {
  const { t } = useLocale()
  const [carrier, setCarrier] = useState('MARU')
  const [trackingNumber, setTrackingNumber] = useState('')
  const [trackingUrl, setTrackingUrl] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const create = async (e) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await adminCreateShipment(order.id, {
        carrier,
        tracking_number: trackingNumber || null,
        tracking_url: trackingUrl || null,
      })
      setCarrier('MARU')
      setTrackingNumber('')
      setTrackingUrl('')
      await onChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.orderDetail.shipmentFailed')))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <h2 className="font-semibold mb-3">{t('admin.orderDetail.shipments')}</h2>
      {order.shipments.length === 0 ? (
        <p className="text-sm text-gray-500 mb-3">{t('admin.orderDetail.noShipments')}</p>
      ) : (
        <ul className="space-y-3 mb-4">
          {order.shipments.map((s) => <ShipmentCard key={s.id} orderId={order.id} shipment={s} onChanged={onChanged} />)}
        </ul>
      )}
      <form onSubmit={create}>
        <h3 className="text-sm font-medium mb-2">{t('admin.orderDetail.addShipment')}</h3>
        <p className="text-xs text-gray-500 mb-2">{t('admin.orderDetail.shipmentHint')}</p>
        <input required value={carrier} onChange={(e) => setCarrier(e.target.value)} placeholder={t('admin.orderDetail.carrier')} aria-label={t('admin.orderDetail.carrier')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
        <input value={trackingNumber} onChange={(e) => setTrackingNumber(e.target.value)} placeholder={t('admin.orderDetail.trackingNumber')} aria-label={t('admin.orderDetail.trackingNumber')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
        <input value={trackingUrl} onChange={(e) => setTrackingUrl(e.target.value)} placeholder={t('admin.orderDetail.trackingUrl')} aria-label={t('admin.orderDetail.trackingUrl')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
        {error && <p role="alert" className="text-sm text-red-600 mb-2">{error}</p>}
        <button type="submit" disabled={busy} className="bg-brand text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-40">{t('admin.orderDetail.createShipment')}</button>
      </form>
    </div>
  )
}
