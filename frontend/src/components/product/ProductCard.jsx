import { Link } from 'react-router-dom'

function cheapestSku(product) {
  const skus = product.variants.flatMap((v) => v.skus)
  return skus.reduce((min, s) => (!min || Number(s.retail_price) < Number(min.retail_price) ? s : min), null)
}

export default function ProductCard({ product }) {
  const sku = cheapestSku(product)
  const variant = product.variants[0]
  const inStock = sku ? sku.available_quantity > 0 : false

  return (
    <Link
      to={`/products/${product.slug}`}
      className="block border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition"
    >
      <div className="aspect-square bg-gray-100 flex items-center justify-center overflow-hidden">
        {variant?.photo_url ? (
          <img src={variant.photo_url} alt={product.name} className="w-full h-full object-cover" />
        ) : (
          <span className="text-gray-400 text-sm">No image</span>
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
            {inStock ? 'In stock' : 'Out of stock'}
          </span>
        </div>
      </div>
    </Link>
  )
}
