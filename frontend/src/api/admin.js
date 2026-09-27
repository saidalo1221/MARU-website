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

// Products
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

// Variants
export function adminUpdateVariant(variantId, payload) {
  return apiRequest(`/admin/variants/${variantId}`, { method: 'PATCH', body: payload })
}
export function adminCreateVariant(productId, payload) {
  return apiRequest(`/admin/products/${productId}/variants`, { method: 'POST', body: payload })
}
export function adminCreateSku(variantId, payload) {
  return apiRequest(`/admin/variants/${variantId}/skus`, { method: 'POST', body: payload })
}

// SKUs
export function adminUpdateSku(skuId, payload) {
  return apiRequest(`/admin/skus/${skuId}`, { method: 'PATCH', body: payload })
}

// Inventory
export function adminListInventory(skuId) {
  return apiRequest(`/admin/inventory/${skuId}`)
}
export function adminAddInventory(skuId, payload) {
  return apiRequest(`/admin/inventory/${skuId}`, { method: 'POST', body: payload })
}
export function adminUpdateInventory(skuId, warehouseId, payload) {
  return apiRequest(`/admin/inventory/${skuId}/${warehouseId}`, { method: 'PATCH', body: payload })
}

// Promo codes
export function adminListPromoCodes() {
  return apiRequest('/admin/promo-codes/')
}
export function adminCreatePromoCode(payload) {
  return apiRequest('/admin/promo-codes/', { method: 'POST', body: payload })
}
export function adminUpdatePromoCode(promoId, payload) {
  return apiRequest(`/admin/promo-codes/${promoId}`, { method: 'PATCH', body: payload })
}

// Shipping rates
export function adminListShippingRates() {
  return apiRequest('/admin/shipping-rates/')
}
export function adminCreateShippingRate(payload) {
  return apiRequest('/admin/shipping-rates/', { method: 'POST', body: payload })
}
export function adminUpdateShippingRate(rateId, payload) {
  return apiRequest(`/admin/shipping-rates/${rateId}`, { method: 'PATCH', body: payload })
}

// Tax rules
export function adminListTaxRules() {
  return apiRequest('/admin/tax-rules/')
}
export function adminCreateTaxRule(payload) {
  return apiRequest('/admin/tax-rules/', { method: 'POST', body: payload })
}
export function adminUpdateTaxRule(ruleId, payload) {
  return apiRequest(`/admin/tax-rules/${ruleId}`, { method: 'PATCH', body: payload })
}

// Exchange rates
export function adminListExchangeRates() {
  return apiRequest('/admin/exchange-rates/')
}
export function adminCreateExchangeRate(payload) {
  return apiRequest('/admin/exchange-rates/', { method: 'POST', body: payload })
}
export function adminUpdateExchangeRate(rateId, unitsPerUsd) {
  return apiRequest(`/admin/exchange-rates/${rateId}`, { method: 'PATCH', body: { units_per_usd: unitsPerUsd } })
}
export function adminSyncExchangeRates() {
  return apiRequest('/admin/exchange-rates/sync', { method: 'POST' })
}

// Notification templates
export function adminListNotificationTemplates(event) {
  const qs = event ? `?event=${encodeURIComponent(event)}` : ''
  return apiRequest(`/admin/notification-templates/${qs}`)
}
export function adminCreateNotificationTemplate(payload) {
  return apiRequest('/admin/notification-templates/', { method: 'POST', body: payload })
}
export function adminUpdateNotificationTemplate(templateId, payload) {
  return apiRequest(`/admin/notification-templates/${templateId}`, { method: 'PATCH', body: payload })
}

// Integration logs
export function adminListIntegrationLogs(statusFilter, integration) {
  const params = new URLSearchParams()
  if (statusFilter) params.set('status_filter', statusFilter)
  if (integration) params.set('integration', integration)
  const qs = params.toString() ? `?${params.toString()}` : ''
  return apiRequest(`/admin/integration-logs/${qs}`)
}
export function adminRetryIntegrationLog(logId) {
  return apiRequest(`/admin/integration-logs/${logId}/retry`, { method: 'POST' })
}

// Audit log
export function adminListAuditLogs(entity) {
  const qs = entity ? `?entity=${encodeURIComponent(entity)}` : ''
  return apiRequest(`/admin/audit-logs/${qs}`)
}

// Analytics events
export function adminListAnalyticsEvents(eventName) {
  const qs = eventName ? `?event_name=${encodeURIComponent(eventName)}` : ''
  return apiRequest(`/admin/analytics-events/${qs}`)
}
