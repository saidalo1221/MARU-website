import { useLocale } from '../context/LocaleContext'
import { formatDateTime } from '../lib/format'

// Customer-facing shipment cards with a per-parcel event timeline. Shared by
// the order page and the public Track Order page.
export default function ShipmentList({ shipments }) {
  const { t } = useLocale()

  if (!shipments?.length) return <p className="text-sm text-gray-500">{t('orderStatus.noShipments')}</p>

  return (
    <ul className="space-y-4">
      {shipments.map((s) => (
        <li key={s.id} className="border border-gray-200 rounded-lg p-4 text-sm">
          <div className="flex justify-between mb-1">
            <span className="font-medium">{s.carrier}</span>
            <span className="font-medium">{t(`orderStatus.shipmentStatus.${s.status}`)}</span>
          </div>
          {s.tracking_number && (
            <p className="text-gray-500">
              {t('orderStatus.trackingNumber')}: <span className="text-gray-900">{s.tracking_number}</span>
            </p>
          )}
          {s.tracking_url && (
            <a href={s.tracking_url} target="_blank" rel="noopener noreferrer" className="text-brand underline">
              {t('orderStatus.trackWithCarrier')}
            </a>
          )}
          {s.events?.length > 0 && (
            <ol className="mt-3 border-l border-gray-200 pl-3 space-y-2 text-xs text-gray-500">
              {[...s.events].reverse().map((e, i) => (
                <li key={i}>
                  <span className="text-gray-900">{t(`orderStatus.shipmentStatus.${e.status}`)}</span>
                  {e.location ? ` · ${e.location}` : ''} · {formatDateTime(e.occurred_at)}
                  {e.note ? <span className="block">{e.note}</span> : null}
                </li>
              ))}
            </ol>
          )}
        </li>
      ))}
    </ul>
  )
}
