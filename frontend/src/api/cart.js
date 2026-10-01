import { apiRequest } from './client'

export function getCart({ promoCode, country, deliveryMethod, region, loyaltyPoints } = {}) {
  const params = new URLSearchParams()
  if (promoCode) params.set('promo_code', promoCode)
  if (country) params.set('country', country)
  if (deliveryMethod) params.set('delivery_method', deliveryMethod)
  if (region) params.set('region', region)
  if (loyaltyPoints) params.set('loyalty_points', String(loyaltyPoints))
  // Product names in the cart follow the language the visitor picked.
  try {
    const lang = localStorage.getItem('maru_locale')
    if (lang) params.set('lang', lang)
  } catch {
    // storage blocked: the cart simply shows default-language names
  }
  const qs = params.toString() ? `?${params.toString()}` : ''
  return apiRequest(`/cart/${qs}`)
}

export function getCartRecommendations({ lang, currency, limit } = {}) {
  const params = new URLSearchParams()
  if (lang) params.set('lang', lang)
  if (currency) params.set('currency', currency)
  if (limit) params.set('limit', limit)
  const qs = params.toString() ? `?${params.toString()}` : ''
  return apiRequest(`/cart/recommendations${qs}`)
}

export function addCartItem(skuId, quantity) {
  return apiRequest('/cart/items', { method: 'POST', body: { sku_id: skuId, quantity } })
}

export function updateCartItem(skuId, quantity) {
  return apiRequest(`/cart/items/${skuId}`, { method: 'PATCH', body: { quantity } })
}

export function removeCartItem(skuId) {
  return apiRequest(`/cart/items/${skuId}`, { method: 'DELETE' })
}

export function saveCartItemForLater(skuId) {
  return apiRequest(`/cart/items/${skuId}/save-for-later`, { method: 'POST' })
}

export function moveSavedItemToCart(skuId) {
  return apiRequest(`/cart/items/${skuId}/move-to-cart`, { method: 'POST' })
}

export function setCartCurrency(currency) {
  return apiRequest('/cart/currency', { method: 'PATCH', body: { currency } })
}

export function mergeCart() {
  return apiRequest('/cart/merge', { method: 'POST' })
}
