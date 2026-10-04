import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link } from 'react-router-dom'
import { useLocale } from '../../context/LocaleContext'
import { useCart } from '../../context/CartContext'
import ProductGallery from './ProductGallery'
import ProductBadges from './ProductBadges'
import VariantSelector from './VariantSelector'
import QuantitySelector from './QuantitySelector'
import useDialogFocus from '../../lib/useDialogFocus'

// Self-contained quick-view: opened from a ProductCard with the product data
// the catalog/search list already fetched (variants+skus included), so no
// extra network round-trip is needed just to preview it.
export default function QuickViewModal({ product, onClose }) {
  const { t } = useLocale()
  const { addItem } = useCart()
  const [variantId, setVariantId] = useState(product.variants[0]?.id ?? null)
  const [quantity, setQuantity] = useState(product.min_order_quantity || 1)
  const [status, setStatus] = useState(null)
  const closeRef = useRef(null)
  const dialogRef = useRef(null)
  useDialogFocus(dialogRef)

  useEffect(() => {
    closeRef.current?.focus()
  }, [])

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  const variant = useMemo(
    () => product.variants.find((v) => v.id === variantId) ?? null,
    [product, variantId]
  )
  const sku = variant?.skus.find((s) => s.is_active) ?? null
  const inStock = sku ? sku.available_quantity > 0 : false

  const handleAddToCart = async () => {
    if (!sku) return
    setStatus(null)
    try {
      await addItem(sku.id, quantity)
      setStatus({ type: 'success', message: t('productDetail.addedToCart') })
    } catch {
      setStatus({ type: 'error', message: t('productDetail.addToCartError') })
    }
  }

  // Rendered under <body>: inside a product card (which lifts on hover with a transform) a fixed-position
  // popup would be sized and clipped by the card instead of covering the page.
  return createPortal(
    <div
      ref={dialogRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={product.name}
    >
      <div
        className="relative max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-3xl bg-page p-6 shadow-xl md:p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          ref={closeRef}
          type="button"
          onClick={onClose}
          aria-label={t('product.quickViewClose')}
          className="absolute right-4 top-4 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-gray-100 text-lg leading-none text-gray-600 transition-colors hover:bg-gray-200"
        >
          ✕
        </button>

        <div className="grid sm:grid-cols-2 gap-6">
          <ProductGallery variant={variant} alt={product.name} />

          <div>
            <ProductBadges badges={product.badges} className="mb-2" />
            <h2 className="pr-10 text-2xl font-semibold tracking-tight">{product.name}</h2>
            <p className="mt-3 text-3xl font-semibold">
              {sku ? `${sku.currency} ${Number(sku.retail_price).toFixed(2)}` : '-'}
            </p>
            <p className={`text-sm mt-1 ${inStock ? 'text-green-700' : 'text-red-600'}`}>
              {inStock ? t('productDetail.inStockCount', { n: sku.available_quantity }) : t('productDetail.outOfStock')}
            </p>

            {product.variants.length > 1 && (
              <div className="mt-4">
                <VariantSelector variants={product.variants} selectedVariantId={variantId} onSelect={setVariantId} />
              </div>
            )}

            <div className="mt-4">
              <p className="text-sm font-medium mb-2">{t('productDetail.quantity')}</p>
              <QuantitySelector
                value={quantity}
                min={product.min_order_quantity || 1}
                max={sku ? sku.available_quantity : undefined}
                onChange={setQuantity}
              />
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleAddToCart}
                disabled={!inStock}
                className="flex-1 rounded-full bg-brand py-3 font-semibold text-white transition-colors hover:bg-brand-dark active:scale-[0.98] disabled:opacity-40"
              >
                {t('productDetail.addToCart')}
              </button>
            </div>

            {status && (
              <p role={status.type === 'success' ? 'status' : 'alert'} className={`text-sm mt-2 ${status.type === 'success' ? 'text-green-700' : 'text-red-600'}`}>
                {status.message}
              </p>
            )}

            <Link to={`/products/${product.slug}`} className="block text-sm text-brand mt-4 underline">
              {t('product.viewFullDetails')}
            </Link>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}
