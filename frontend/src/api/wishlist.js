import { apiRequest } from './client'

function buildQuery({ lang, currency } = {}) {
  const params = new URLSearchParams()
  if (lang) params.set('lang', lang)
  if (currency) params.set('currency', currency)
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export function getWishlist(lang, currency) {
  return apiRequest(`/wishlist/${buildQuery({ lang, currency })}`)
}

export function addToWishlist(skuId, lang, currency) {
  return apiRequest(`/wishlist/${skuId}${buildQuery({ lang, currency })}`, { method: 'POST' })
}

export function removeFromWishlist(skuId, lang, currency) {
  return apiRequest(`/wishlist/${skuId}${buildQuery({ lang, currency })}`, { method: 'DELETE' })
}
