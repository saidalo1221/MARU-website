import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { getWishlist, removeFromWishlist } from '../api/wishlist'
import { markWishlist } from '../lib/wishlistStore'
import { useCart } from '../context/CartContext'
import AccountNav from '../components/account/AccountNav'
import Seo from '../components/Seo'

export default function Wishlist() {
  const { user, loading: authLoading } = useAuth()
  const { locale, t } = useLocale()
  const { cart, addItem } = useCart()
  const currency = cart?.currency
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState(null)

  useEffect(() => {
    if (!user) return
    setLoading(true)
    getWishlist(locale, currency).then(setItems).finally(() => setLoading(false))
  }, [user, locale, currency])

  if (authLoading) return null
  if (!user) return <Navigate to="/login" replace />

  const handleRemove = async (skuId) => {
    const updated = await removeFromWishlist(skuId, locale, currency)
    markWishlist(skuId, false)
    setItems(updated)
  }

  const handleAddToCart = async (skuId) => {
    setStatus(null)
    try {
      await addItem(skuId, 1)
      setStatus({ type: 'success', message: t('productDetail.addedToCart') })
    } catch {
      setStatus({ type: 'error', message: t('productDetail.addToCartError') })
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Seo title={t('wishlist.title')} noindex />
      <AccountNav />
      <h1 className="text-2xl font-bold mb-6">{t('wishlist.title')}</h1>
      {loading && <p>{t('wishlist.loading')}</p>}
      {!loading && items.length === 0 && <p className="text-gray-500">{t('wishlist.empty')}</p>}
      {status && (
        <p role={status.type === 'success' ? 'status' : 'alert'} className={`text-sm mb-4 ${status.type === 'success' ? 'text-green-700' : 'text-red-600'}`}>
          {status.message}
        </p>
      )}
      <ul className="divide-y divide-gray-200">
        {items.map((item) => (
          <li key={item.sku_id} className="py-4 flex items-center justify-between gap-4">
            <div>
              <Link to={`/products/${item.product_slug}`} className="font-medium text-sm hover:text-brand">
                {item.product_name}
              </Link>
              <p className="text-xs text-gray-500">{item.sku_code}</p>
              <p className="text-sm mt-1">{item.currency} {Number(item.price).toFixed(2)}</p>
              <p className={`text-xs ${item.in_stock ? 'text-green-700' : 'text-red-600'}`}>
                {item.in_stock ? t('product.inStock') : t('product.outOfStock')}
              </p>
            </div>
            <div className="flex flex-col gap-2 items-end">
              <button
                onClick={() => handleAddToCart(item.sku_id)}
                disabled={!item.in_stock}
                className="border border-brand text-brand rounded px-3 py-1.5 text-sm disabled:opacity-40"
              >
                {t('productDetail.addToCart')}
              </button>
              <button onClick={() => handleRemove(item.sku_id)} className="text-red-600 text-sm">
                {t('cart.remove')}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
