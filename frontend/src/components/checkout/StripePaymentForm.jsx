import { useEffect, useRef, useState } from 'react'
import { loadScript } from '../../lib/loadScript'
import { useLocale } from '../../context/LocaleContext'

const PUBLISHABLE_KEY = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY

export default function StripePaymentForm({ clientSecret, onSuccess, onError }) {
  const { t } = useLocale()
  const cardElementRef = useRef(null)
  const stripeRef = useRef(null)
  const cardRef = useRef(null)
  const [ready, setReady] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!PUBLISHABLE_KEY) {
      onError(t('stripe.notConfigured'))
      return
    }
    let cancelled = false
    loadScript('https://js.stripe.com/v3/').then(() => {
      if (cancelled) return
      const stripe = window.Stripe(PUBLISHABLE_KEY)
      stripeRef.current = stripe
      const elements = stripe.elements()
      const card = elements.create('card')
      card.mount(cardElementRef.current)
      cardRef.current = card
      setReady(true)
    })
    return () => {
      cancelled = true
      cardRef.current?.unmount()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!stripeRef.current || !cardRef.current) return
    setSubmitting(true)
    const { error, paymentIntent } = await stripeRef.current.confirmCardPayment(clientSecret, {
      payment_method: { card: cardRef.current },
    })
    setSubmitting(false)
    if (error) {
      onError(error.message || t('stripe.paymentFailed'))
      return
    }
    if (paymentIntent?.status === 'succeeded' || paymentIntent?.status === 'processing') {
      onSuccess()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div ref={cardElementRef} className="border border-gray-300 rounded px-3 py-3" />
      <button
        type="submit"
        disabled={!ready || submitting}
        className="w-full bg-brand text-white rounded py-3 font-medium disabled:opacity-40"
      >
        {submitting ? t('checkout.processing') : t('checkout.payNow')}
      </button>
    </form>
  )
}
