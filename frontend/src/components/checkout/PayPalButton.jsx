import { useEffect, useRef } from 'react'
import { loadScript } from '../../lib/loadScript'

const CLIENT_ID = import.meta.env.VITE_PAYPAL_CLIENT_ID

export default function PayPalButton({ providerOrderId, onApprove, onError }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!CLIENT_ID) {
      onError('PayPal is not configured (missing VITE_PAYPAL_CLIENT_ID).')
      return
    }
    let cancelled = false
    loadScript(`https://www.paypal.com/sdk/js?client-id=${CLIENT_ID}&currency=USD`).then(() => {
      if (cancelled || !containerRef.current) return
      window.paypal
        .Buttons({
          createOrder: () => providerOrderId,
          onApprove: () => onApprove(),
          onError: (err) => onError(err?.message || 'PayPal payment failed'),
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
