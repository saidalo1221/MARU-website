import { apiRequest } from './client'

export function checkout(payload) {
  return apiRequest('/orders/', { method: 'POST', body: payload })
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

export function listMyOrders() {
  return apiRequest('/orders/me')
}

export function getMyOrder(orderId) {
  return apiRequest(`/orders/me/${orderId}`)
}

export function getPaymentMethods() {
  return apiRequest('/payments/methods')
}
