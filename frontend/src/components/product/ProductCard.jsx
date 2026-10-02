import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'
import { useLocale } from '../../context/LocaleContext'
import Picture from '../ui/Picture'
import { toggleWishlist, useWishlistSkus } from '../../lib/wishlistStore'
import Rating from '../ui/Rating'
import { useToast } from '../ui/Toast'
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
  const toast = useToast()
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
      toast(t('productDetail.addToCartError'), 'error')
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
      toast(t('wishlist.failed'), 'error')
    }
  }

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-3xl border border-gray-200 bg-gray-50 transition duration-base hover:-translate-y-1 hover:shadow-token">
      <ProductBadges badges={product.badges} className="absolute top-5 left-5 z-10" />
      {sku && (
        <button
          type="button"
          onClick={handleWishlist}
          aria-pressed={wishlisted}
          aria-label={wishlisted ? t('wishlist.remove') : t('wishlist.add')}
          className={`absolute top-5 right-5 z-10 h-9 w-9 rounded-full bg-white/90 text-xl leading-none shadow ${wishlisted ? 'text-red-600' : 'text-gray-500'}`}
        >
          {wishlisted ? '♥' : '♡'}
        </button>
      )}

      <Link to={`/products/${product.slug}`} className="block flex-1">
        <div className="m-2 flex aspect-square items-center justify-center overflow-hidden rounded-2xl bg-gray-100">
          {coverImage ? (
            <Picture src={coverImage} sizes="(min-width: 1024px) 25vw, (min-width: 640px) 33vw, 50vw" alt={product.name} loading="lazy" decoding="async" className="w-full h-full object-cover" />
          ) : (
            <span className="text-gray-500 text-sm">{t('product.noImage')}</span>
          )}
        </div>
        <div className="px-4 pb-3 pt-2">
          <h3 className="truncate font-semibold">{product.name}</h3>
          <p className="text-sm text-gray-500">{product.volume_ml} ml</p>
          <Rating value={product.rating_average} count={product.rating_count} className="mt-0.5" />
          <div className="mt-2 flex flex-wrap items-baseline justify-between gap-2">
            <span className="text-lg font-semibold">
              {sku ? `${sku.currency} ${Number(onSale ? sku.special_price : sku.retail_price).toFixed(2)}` : '-'}
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
          className="mx-3 block rounded-full bg-brand py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark active:scale-[0.98] disabled:opacity-50"
        >
          {added ? t('product.added') : t('productDetail.addToCart')}
        </button>
      )}
      <button
        type="button"
        onClick={() => setQuickViewOpen(true)}
        className="block w-full py-3 text-xs font-medium text-brand hover:underline"
      >
        {t('product.quickView')}
      </button>

      {quickViewOpen && <QuickViewModal product={product} onClose={() => setQuickViewOpen(false)} />}
    </div>
  )
}
