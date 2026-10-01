import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'
import { useLocale } from '../../context/LocaleContext'
import { toggleWishlist, useWishlistSkus } from '../../lib/wishlistStore'
import ProductBadges from './ProductBadges'
import QuickViewModal from './QuickViewModal'

function cheapestSku(product) {
  const skus = product.variants.flatMap((v) => v.skus)
  return skus.reduce((min, s) => (!min || Number(s.retail_price) < Number(min.retail_price) ? s : min), null)
}

export default function ProductCard({ product }) {
  const { t } = useLocale()
  const { user } = useAuth()
  const { addItem } = useCart()
  const navigate = useNavigate()
  const wishlist = useWishlistSkus(user)
  const [quickViewOpen, setQuickViewOpen] = useState(false)
  const [adding, setAdding] = useState(false)
  const [added, setAdded] = useState(false)
  const sku = cheapestSku(product)
  const variant = product.variants[0]
  const coverImage = variant?.images?.[0]?.image_url || variant?.photo_url
  const inStock = sku ? sku.available_quantity > 0 : false
  const onSale = sku && sku.special_price != null && Number(sku.special_price) < Number(sku.retail_price)
  const discount = onSale ? Math.round((1 - Number(sku.special_price) / Number(sku.retail_price)) * 100) : 0
  const skuCount = product.variants.reduce((n, v) => n + v.skus.length, 0)
  const canQuickAdd = inStock && skuCount === 1
  const wishlisted = sku ? wishlist.has(sku.id) : false

  const handleAdd = async () => {
    setAdding(true)
    try {
      await addItem(sku.id, product.min_order_quantity || 1)
      setAdded(true)
      setTimeout(() => setAdded(false), 2000)
    } catch {
      // The cart context surfaces its own error state; nothing more to do on the card.
    } finally {
      setAdding(false)
    }
  }

  const handleWishlist = async () => {
    if (!user) {
      navigate('/login')
      return
    }
    try {
      await toggleWishlist(sku.id)
    } catch {
      // Leave the heart as it was; the next click retries.
    }
  }

  return (
    <div className="relative border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition group">
      <ProductBadges badges={product.badges} className="absolute top-2 left-2 z-10" />
      {sku && (
        <button
          type="button"
          onClick={handleWishlist}
          aria-pressed={wishlisted}
          aria-label={wishlisted ? t('wishlist.remove') : t('wishlist.add')}
          className={`absolute top-2 right-2 z-10 h-9 w-9 rounded-full bg-white/90 text-xl leading-none shadow ${wishlisted ? 'text-red-600' : 'text-gray-500'}`}
        >
          {wishlisted ? '♥' : '♡'}
        </button>
      )}

      <Link to={`/products/${product.slug}`} className="block">
        <div className="aspect-square bg-gray-100 flex items-center justify-center overflow-hidden">
          {coverImage ? (
            <img src={coverImage} alt={product.name} className="w-full h-full object-cover" />
          ) : (
            <span className="text-gray-500 text-sm">{t('product.noImage')}</span>
          )}
        </div>
        <div className="p-3">
          <h3 className="font-medium text-sm truncate">{product.name}</h3>
          <p className="text-xs text-gray-500">{product.volume_ml} ml</p>
          {product.rating_count > 0 && (
            <p
              className="text-xs text-yellow-600 mt-0.5"
              role="img"
              aria-label={t('product.ratingLabel', { avg: product.rating_average, n: product.rating_count })}
            >
              <span aria-hidden="true">★ {product.rating_average} ({product.rating_count})</span>
            </p>
          )}
          <div className="flex items-center justify-between gap-2 flex-wrap mt-2">
            <span className="font-semibold">
              {sku ? `${sku.currency} ${Number(onSale ? sku.special_price : sku.retail_price).toFixed(2)}` : '—'}
              {onSale && (
                <>
                  {' '}
                  <s className="text-xs font-normal text-gray-500">{Number(sku.retail_price).toFixed(2)}</s>{' '}
                  <span className="text-xs font-medium text-red-600">−{discount}%</span>
                </>
              )}
            </span>
            <span className={`text-xs ${inStock ? 'text-green-700' : 'text-red-600'}`}>
              {inStock ? t('product.inStock') : t('product.outOfStock')}
            </span>
          </div>
        </div>
      </Link>

      {canQuickAdd && (
        <button
          type="button"
          onClick={handleAdd}
          disabled={adding}
          className="block w-full bg-brand text-white py-2 text-sm font-medium disabled:opacity-50"
        >
          {added ? t('product.added') : t('productDetail.addToCart')}
        </button>
      )}
      <button
        type="button"
        onClick={() => setQuickViewOpen(true)}
        className="block w-full border-t border-gray-200 py-2 text-xs font-medium text-brand hover:bg-gray-50"
      >
        {t('product.quickView')}
      </button>

      {quickViewOpen && <QuickViewModal product={product} onClose={() => setQuickViewOpen(false)} />}
    </div>
  )
}
