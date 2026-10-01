import { apiRequest } from './client'

export function checkout(payload, idempotencyKey) {
  return apiRequest('/orders/', { method: 'POST', body: payload, idempotencyKey })
}

export function getOrder(orderId, orderToken) {
  return apiRequest(`/orders/${orderId}`, { orderToken })
}

export function confirmPayment(orderId, orderToken) {
  return apiRequest(`/orders/${orderId}/confirm-payment`, { method: 'POST', orderToken })
}

export function cancelOrder(orderId, orderToken) {
  return apiRequest(`/orders/${orderId}/cancel`, { method: 'POST', orderToken })
}

export function trackOrder(orderNumber, email) {
  return apiRequest('/orders/track', { method: 'POST', body: { order_number: orderNumber, email } })
}

export function listMyOrders() {
  return apiRequest('/orders/me')
}

export function getMyOrder(orderId) {
  return apiRequest(`/orders/me/${orderId}`)
}

export function getPaymentMethods() {
  return apiRequest('/payments/methods')
}

export function retryPayment(orderId, orderToken) {
  return apiRequest(`/orders/${orderId}/payment`, { method: 'POST', orderToken })
}
