import { apiRequest } from './client'

// Admin session / users
export function adminSessionCheck() {
  return apiRequest('/admin/users/session')
}
export function adminListAdmins() {
  return apiRequest('/admin/users/admins')
}
export function adminPromoteUser(email, role) {
  return apiRequest('/admin/users/promote', { method: 'POST', body: { email, role } })
}
export function adminDemoteUser(userId) {
  return apiRequest(`/admin/users/${userId}/demote`, { method: 'POST' })
}

// Site settings
export function adminGetSiteSettings() {
  return apiRequest('/admin/site-settings')
}
export function adminUpdateSiteSettings(payload) {
  return apiRequest('/admin/site-settings', { method: 'PATCH', body: payload })
}
export function adminListSiteSettingsTranslations() {
  return apiRequest('/admin/site-settings/translations')
}
export function adminUpsertSiteSettingsTranslation(locale, payload) {
  return apiRequest(`/admin/site-settings/translations/${locale}`, { method: 'PUT', body: payload })
}

// Orders
// Paged lists resolve to { data, total } (see apiRequest `meta`).
function pagedQuery(statusFilter, page, extra = {}) {
  const params = new URLSearchParams()
  if (statusFilter) params.set('status_filter', statusFilter)
  Object.entries(extra).forEach(([k, v]) => v && params.set(k, v))
  if (page > 1) params.set('page', String(page))
  return params.toString() ? `?${params.toString()}` : ''
}
export function adminListOrders(statusFilter, page = 1) {
  return apiRequest(`/admin/orders/${pagedQuery(statusFilter, page)}`, { meta: true })
}
export function adminGetOrder(orderId) {
  return apiRequest(`/admin/orders/${orderId}`)
}
export function adminUpdateOrderStatus(orderId, status, note) {
  return apiRequest(`/admin/orders/${orderId}/status`, { method: 'PATCH', body: { status, note: note || null } })
}
export function adminCreateShipment(orderId, body) {
  return apiRequest(`/admin/orders/${orderId}/shipments`, { method: 'POST', body })
}
export function adminAddShipmentEvent(orderId, shipmentId, body) {
  return apiRequest(`/admin/orders/${orderId}/shipments/${shipmentId}/events`, { method: 'POST', body })
}
export function adminRefundOrder(orderId, amount, reason) {
  return apiRequest(`/admin/orders/${orderId}/refund`, { method: 'POST', body: { amount, reason: reason || null } })
}

// Quotes
export function adminListQuotes(statusFilter, page = 1) {
  return apiRequest(`/admin/quotes/${pagedQuery(statusFilter, page)}`, { meta: true })
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
export function adminListReviews(statusFilter, page = 1) {
  return apiRequest(`/admin/reviews/${pagedQuery(statusFilter, page)}`, { meta: true })
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
export function adminListCategoryTranslations(categoryId) {
  return apiRequest(`/admin/categories/${categoryId}/translations`)
}
export function adminUpsertCategoryTranslation(categoryId, locale, payload) {
  return apiRequest(`/admin/categories/${categoryId}/translations/${locale}`, { method: 'PUT', body: payload })
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

// Uploads
export function adminUploadImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  return apiRequest('/admin/uploads/image', { method: 'POST', body: formData })
}

export function adminUploadVideo(file) {
  const formData = new FormData()
  formData.append('file', file)
  return apiRequest('/admin/uploads/video', { method: 'POST', body: formData })
}

// Product translations
export function adminListProductTranslations(productId) {
  return apiRequest(`/admin/products/${productId}/translations`)
}
export function adminUpsertProductTranslation(productId, locale, payload) {
  return apiRequest(`/admin/products/${productId}/translations/${locale}`, { method: 'PUT', body: payload })
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

export function adminReplaceSkuTiers(skuId, tiers) {
  return apiRequest(`/admin/skus/${skuId}/tiers`, { method: 'PUT', body: { tiers } })
}

// Variant image gallery
export function adminAddVariantImage(variantId, imageUrl) {
  return apiRequest(`/admin/variants/${variantId}/images`, { method: 'POST', body: { image_url: imageUrl } })
}
export function adminReorderVariantImage(variantId, imageId, sortOrder) {
  return apiRequest(`/admin/variants/${variantId}/images/${imageId}`, {
    method: 'PATCH',
    body: { sort_order: sortOrder },
  })
}
export function adminDeleteVariantImage(variantId, imageId) {
  return apiRequest(`/admin/variants/${variantId}/images/${imageId}`, { method: 'DELETE' })
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
export function adminListAvailableCurrencies() {
  return apiRequest('/admin/exchange-rates/available-currencies')
}
export function adminDeleteExchangeRate(rateId) {
  return apiRequest(`/admin/exchange-rates/${rateId}`, { method: 'DELETE' })
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
export function adminListIntegrationLogs(statusFilter, integration, page = 1) {
  return apiRequest(`/admin/integration-logs/${pagedQuery(statusFilter, page, { integration })}`, { meta: true })
}
export function adminJobStats() {
  return apiRequest('/admin/jobs/stats')
}
export function adminListDeadJobs() {
  return apiRequest('/admin/jobs/?status_filter=dead')
}
export function adminRetryJob(id) {
  return apiRequest(`/admin/jobs/${id}/retry`, { method: 'POST' })
}
export function adminIntegrationHealth() {
  return apiRequest('/admin/integration-logs/health')
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
export function adminListNewsletter(statusFilter) {
  const qs = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : ''
  return apiRequest(`/admin/newsletter/${qs}`)
}

export function adminListAnalyticsEvents(eventName) {
  const qs = eventName ? `?event_name=${encodeURIComponent(eventName)}` : ''
  return apiRequest(`/admin/analytics-events/${qs}`)
}

// About sections
export function adminListAboutSections(lang) {
  const qs = lang ? `?lang=${encodeURIComponent(lang)}` : ''
  return apiRequest(`/admin/about-sections${qs}`)
}
export function adminCreateAboutSection(payload) {
  return apiRequest('/admin/about-sections', { method: 'POST', body: payload })
}
export function adminUpdateAboutSection(sectionId, payload) {
  return apiRequest(`/admin/about-sections/${sectionId}`, { method: 'PATCH', body: payload })
}
export function adminDeleteAboutSection(sectionId) {
  return apiRequest(`/admin/about-sections/${sectionId}`, { method: 'DELETE' })
}
export function adminMoveAboutSection(sectionId, direction) {
  return apiRequest(`/admin/about-sections/${sectionId}/move`, { method: 'POST', body: { direction } })
}
export function adminListAboutSectionTranslations(sectionId) {
  return apiRequest(`/admin/about-sections/${sectionId}/translations`)
}
export function adminUpsertAboutSectionTranslation(sectionId, locale, payload) {
  return apiRequest(`/admin/about-sections/${sectionId}/translations/${locale}`, { method: 'PUT', body: payload })
}

// Page sections (Delivery/Payment/Returns/FAQ/Contact free-form content)
export function adminListPageSections(page, lang) {
  const params = new URLSearchParams({ page })
  if (lang) params.set('lang', lang)
  return apiRequest(`/admin/page-sections?${params.toString()}`)
}
export function adminCreatePageSection(payload) {
  return apiRequest('/admin/page-sections', { method: 'POST', body: payload })
}
export function adminUpdatePageSection(sectionId, payload) {
  return apiRequest(`/admin/page-sections/${sectionId}`, { method: 'PATCH', body: payload })
}
export function adminDeletePageSection(sectionId) {
  return apiRequest(`/admin/page-sections/${sectionId}`, { method: 'DELETE' })
}
export function adminMovePageSection(sectionId, direction) {
  return apiRequest(`/admin/page-sections/${sectionId}/move`, { method: 'POST', body: { direction } })
}
export function adminListPageSectionTranslations(sectionId) {
  return apiRequest(`/admin/page-sections/${sectionId}/translations`)
}
export function adminUpsertPageSectionTranslation(sectionId, locale, payload) {
  return apiRequest(`/admin/page-sections/${sectionId}/translations/${locale}`, { method: 'PUT', body: payload })
}

// Blog categories
export function adminListBlogCategories() {
  return apiRequest('/admin/blog/categories')
}
export function adminCreateBlogCategory(payload) {
  return apiRequest('/admin/blog/categories', { method: 'POST', body: payload })
}
export function adminUpdateBlogCategory(categoryId, payload) {
  return apiRequest(`/admin/blog/categories/${categoryId}`, { method: 'PATCH', body: payload })
}
export function adminDeleteBlogCategory(categoryId) {
  return apiRequest(`/admin/blog/categories/${categoryId}`, { method: 'DELETE' })
}

// Blog posts
export function adminListBlogPosts(page = 1) {
  return apiRequest(`/admin/blog/posts${page > 1 ? `?page=${page}` : ''}`, { meta: true })
}
export function adminGetBlogPost(postId) {
  return apiRequest(`/admin/blog/posts/${postId}`)
}
export function adminCreateBlogPost(payload) {
  return apiRequest('/admin/blog/posts', { method: 'POST', body: payload })
}
export function adminUpdateBlogPost(postId, payload) {
  return apiRequest(`/admin/blog/posts/${postId}`, { method: 'PATCH', body: payload })
}
export function adminDeleteBlogPost(postId) {
  return apiRequest(`/admin/blog/posts/${postId}`, { method: 'DELETE' })
}
export function adminListBlogPostTranslations(postId) {
  return apiRequest(`/admin/blog/posts/${postId}/translations`)
}
export function adminUpsertBlogPostTranslation(postId, locale, payload) {
  return apiRequest(`/admin/blog/posts/${postId}/translations/${locale}`, { method: 'PUT', body: payload })
}
