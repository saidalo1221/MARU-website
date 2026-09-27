import { useEffect, useRef } from 'react'
import { loadScript } from '../../lib/loadScript'
import { useLocale } from '../../context/LocaleContext'

const CLIENT_ID = import.meta.env.VITE_PAYPAL_CLIENT_ID

export default function PayPalButton({ providerOrderId, onApprove, onError }) {
  const { t } = useLocale()
  const containerRef = useRef(null)

  useEffect(() => {
    if (!CLIENT_ID) {
      onError(t('paypal.notConfigured'))
      return
    }
    let cancelled = false
    loadScript(`https://www.paypal.com/sdk/js?client-id=${CLIENT_ID}&currency=USD`).then(() => {
      if (cancelled || !containerRef.current) return
      window.paypal
        .Buttons({
          createOrder: () => providerOrderId,
          onApprove: () => onApprove(),
          onError: (err) => onError(err?.message || t('paypal.paymentFailed')),
        })
        .render(containerRef.current)
    })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [providerOrderId])

  return <div ref={containerRef} />
}
