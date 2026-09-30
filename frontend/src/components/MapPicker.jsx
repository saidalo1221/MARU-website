import { useState } from 'react'
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import { useLocale } from '../context/LocaleContext'

// Vite doesn't resolve Leaflet's default marker image paths the way its own
// bundler expects, so the default icon renders broken/blank unless the URLs
// are set explicitly (a well-known Leaflet + bundler issue).
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({ iconRetinaUrl: markerIcon2x, iconUrl: markerIcon, shadowUrl: markerShadow })

const DEFAULT_CENTER = [41.2995, 69.2401] // Tashkent — used only when no pin is set yet

function ClickHandler({ onPick }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

// Free OpenStreetMap tiles + Nominatim reverse geocoding — no API key or
// billing account needed. Always reports the picked lat/lng via onChange;
// onReverseGeocode is best-effort (network hiccups just skip the autofill,
// the pin itself is unaffected) and only fires when provided.
export default function MapPicker({ latitude, longitude, onChange, onReverseGeocode, height = 260, readOnly = false }) {
  const { t } = useLocale()
  const [geocoding, setGeocoding] = useState(false)
  const position = latitude != null && longitude != null ? [latitude, longitude] : null

  const handlePick = async (lat, lng) => {
    onChange({ latitude: lat, longitude: lng })
    if (!onReverseGeocode) return

    setGeocoding(true)
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&addressdetails=1`
      )
      const data = await res.json()
      const addr = data.address || {}
      onReverseGeocode({
        country: addr.country || '',
        city: addr.city || addr.town || addr.village || addr.county || '',
        addressLine: data.display_name || '',
        postalCode: addr.postcode || '',
      })
    } catch {
      // best-effort — see module docstring
    } finally {
      setGeocoding(false)
    }
  }

  return (
    <div>
      <div style={{ height }} className="rounded-lg overflow-hidden border border-gray-300">
        <MapContainer
          center={position || DEFAULT_CENTER}
          zoom={position ? 15 : 11}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {!readOnly && <ClickHandler onPick={handlePick} />}
          {position && <Marker position={position} />}
        </MapContainer>
      </div>
      {!readOnly && <p className="text-xs text-gray-500 mt-1">{geocoding ? t('map.geocoding') : t('map.clickHint')}</p>}
    </div>
  )
}
