import { apiRequest } from './client'

// Orders
export function adminListOrders(statusFilter) {
  const qs = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : ''
  return apiRequest(`/admin/orders/${qs}`)
}
export function adminGetOrder(orderId) {
  return apiRequest(`/admin/orders/${orderId}`)
}
export function adminUpdateOrderStatus(orderId, status, note) {
  return apiRequest(`/admin/orders/${orderId}/status`, { method: 'PATCH', body: { status, note: note || null } })
}
export function adminRefundOrder(orderId, amount, reason) {
  return apiRequest(`/admin/orders/${orderId}/refund`, { method: 'POST', body: { amount, reason: reason || null } })
}

// Quotes
export function adminListQuotes(statusFilter) {
  const qs = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : ''
  return apiRequest(`/admin/quotes/${qs}`)
}
export function adminGetQuote(quoteId) {
  return apiRequest(`/admin/quotes/${quoteId}`)
}
export function adminUpdateQuote(quoteId, payload) {
  return apiRequest(`/admin/quotes/${quoteId}`, { method: 'PATCH', body: payload })
}
export function adminConvertQuote(quoteId, payload) {
  return apiRequest(`/admin/quotes/${quoteId}/convert`, { method: 'POST', body: payload })
}

// Reviews
export function adminListReviews(statusFilter) {
  const qs = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : ''
  return apiRequest(`/admin/reviews/${qs}`)
}
export function adminModerateReview(reviewId, status) {
  return apiRequest(`/admin/reviews/${reviewId}`, { method: 'PATCH', body: { status } })
}

// Categories
export function adminListCategories() {
  return apiRequest('/categories/')
}
export function adminCreateCategory(payload) {
  return apiRequest('/admin/categories/', { method: 'POST', body: payload })
}
export function adminUpdateCategory(categoryId, payload) {
  return apiRequest(`/admin/categories/${categoryId}`, { method: 'PATCH', body: payload })
}
export function adminDeleteCategory(categoryId) {
  return apiRequest(`/admin/categories/${categoryId}`, { method: 'DELETE' })
}

// Warehouses
export function adminListWarehouses() {
  return apiRequest('/admin/warehouses/')
}
export function adminCreateWarehouse(payload) {
  return apiRequest('/admin/warehouses/', { method: 'POST', body: payload })
}
export function adminUpdateWarehouse(warehouseId, payload) {
  return apiRequest(`/admin/warehouses/${warehouseId}`, { method: 'PATCH', body: payload })
}

// Products (list/basic edit only — variant/SKU/inventory management is a
// separate, larger admin surface not yet built; see TODO.md)
export function adminListProducts() {
  return apiRequest('/admin/products/')
}
export function adminGetProduct(productId) {
  return apiRequest(`/admin/products/${productId}`)
}
export function adminCreateProduct(payload) {
  return apiRequest('/admin/products/', { method: 'POST', body: payload })
}
export function adminUpdateProduct(productId, payload) {
  return apiRequest(`/admin/products/${productId}`, { method: 'PATCH', body: payload })
}
