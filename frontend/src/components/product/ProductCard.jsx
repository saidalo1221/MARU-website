import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useLocale } from '../../context/LocaleContext'
import ProductBadges from './ProductBadges'
import QuickViewModal from './QuickViewModal'

function cheapestSku(product) {
  const skus = product.variants.flatMap((v) => v.skus)
  return skus.reduce((min, s) => (!min || Number(s.retail_price) < Number(min.retail_price) ? s : min), null)
}

export default function ProductCard({ product }) {
  const { t } = useLocale()
  const [quickViewOpen, setQuickViewOpen] = useState(false)
  const sku = cheapestSku(product)
  const variant = product.variants[0]
  const coverImage = variant?.images?.[0]?.image_url || variant?.photo_url
  const inStock = sku ? sku.available_quantity > 0 : false

  return (
    <div className="relative border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition group">
      <ProductBadges badges={product.badges} className="absolute top-2 left-2 z-10" />

      <Link to={`/products/${product.slug}`} className="block">
        <div className="aspect-square bg-gray-100 flex items-center justify-center overflow-hidden">
          {coverImage ? (
            <img src={coverImage} alt={product.name} className="w-full h-full object-cover" />
          ) : (
            <span className="text-gray-400 text-sm">{t('product.noImage')}</span>
          )}
        </div>
        <div className="p-3">
          <h3 className="font-medium text-sm truncate">{product.name}</h3>
          <p className="text-xs text-gray-500">{product.volume_ml} ml</p>
          <div className="flex items-center justify-between mt-2">
            <span className="font-semibold">
              {sku ? `${sku.currency} ${Number(sku.retail_price).toFixed(2)}` : '—'}
            </span>
            <span className={`text-xs ${inStock ? 'text-green-600' : 'text-red-500'}`}>
              {inStock ? t('product.inStock') : t('product.outOfStock')}
            </span>
          </div>
        </div>
      </Link>

      <button
        type="button"
        onClick={() => setQuickViewOpen(true)}
        className="absolute bottom-[4.5rem] right-2 bg-white/90 hover:bg-white text-xs font-medium px-2 py-1 rounded shadow opacity-90 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100 transition"
      >
        {t('product.quickView')}
      </button>

      {quickViewOpen && <QuickViewModal product={product} onClose={() => setQuickViewOpen(false)} />}
    </div>
  )
}
