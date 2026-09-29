import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useLocale } from '../../context/LocaleContext'
import { useCart } from '../../context/CartContext'
import ProductGallery from './ProductGallery'
import ProductBadges from './ProductBadges'
import VariantSelector from './VariantSelector'
import QuantitySelector from './QuantitySelector'

// Self-contained quick-view: opened from a ProductCard with the product data
// the catalog/search list already fetched (variants+skus included), so no
// extra network round-trip is needed just to preview it.
export default function QuickViewModal({ product, onClose }) {
  const { t } = useLocale()
  const { addItem } = useCart()
  const [variantId, setVariantId] = useState(product.variants[0]?.id ?? null)
  const [quantity, setQuantity] = useState(product.min_order_quantity || 1)
  const [status, setStatus] = useState(null)

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

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label={t('product.quickViewClose')}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 text-xl leading-none"
        >
          ✕
        </button>

        <div className="grid sm:grid-cols-2 gap-6">
          <ProductGallery variant={variant} alt={product.name} />

          <div>
            <ProductBadges badges={product.badges} className="mb-2" />
            <h2 className="text-xl font-bold">{product.name}</h2>
            <p className="text-2xl font-semibold mt-2">
              {sku ? `${sku.currency} ${Number(sku.retail_price).toFixed(2)}` : '—'}
            </p>
            <p className={`text-sm mt-1 ${inStock ? 'text-green-600' : 'text-red-500'}`}>
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
                className="flex-1 bg-brand text-white rounded py-2.5 font-medium disabled:opacity-40"
              >
                {t('productDetail.addToCart')}
              </button>
            </div>

            {status && (
              <p className={`text-sm mt-2 ${status.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                {status.message}
              </p>
            )}

            <Link to={`/products/${product.slug}`} className="block text-sm text-brand mt-4 underline">
              {t('product.viewFullDetails')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
