import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import { listProducts } from '../api/products'
import ProductCard from '../components/product/ProductCard'
import InquiryForm from '../components/forms/InquiryForm'
import Seo from '../components/Seo'

export default function Wholesale() {
  const { locale, t } = useLocale()
  const { cart } = useCart()
  const currency = cart?.currency
  const [products, setProducts] = useState([])

  useEffect(() => {
    // The best sellers only: the whole catalogue lives on the shop page, not here.
    listProducts(locale, currency, { sort: 'popularity', limit: 12 }).then(setProducts).catch(() => {})
  }, [locale, currency])

  const benefits = ['wholesale.benefit1', 'wholesale.benefit2', 'wholesale.benefit3', 'wholesale.benefit4']

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <Seo title={t('wholesale.title')} description={t('wholesale.subtitle')} />
      <h1 className="text-3xl font-bold mb-3">{t('wholesale.title')}</h1>
      <p className="text-gray-600 mb-8">{t('wholesale.subtitle')}</p>

      <ul className="grid sm:grid-cols-2 gap-4 mb-10">
        {benefits.map((key) => (
          <li key={key} className="border border-gray-200 rounded-lg p-4 text-sm">{t(key)}</li>
        ))}
      </ul>

      <dl className="grid sm:grid-cols-2 gap-6 mb-10 text-sm">
        <div>
          <dt className="font-semibold mb-1">{t('wholesale.moqTitle')}</dt>
          <dd className="text-gray-600">{t('wholesale.moqText')}</dd>
        </div>
        <div>
          <dt className="font-semibold mb-1">{t('wholesale.packagingTitle')}</dt>
          <dd className="text-gray-600">{t('wholesale.packagingText')}</dd>
        </div>
        <div>
          <dt className="font-semibold mb-1">{t('wholesale.pricingTitle')}</dt>
          <dd className="text-gray-600">{t('wholesale.pricingText')}</dd>
        </div>
        <div>
          <dt className="font-semibold mb-1">{t('productDetail.delivery')}</dt>
          <dd className="text-gray-600">{t('wholesale.deliveryText')}</dd>
        </div>
      </dl>

      {products.length > 0 && (
        <div className="mb-10 overflow-x-auto">
          <h2 className="text-xl font-semibold mb-3">{t('wholesale.tableTitle')}</h2>
          <table className="w-full text-sm border border-gray-200">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th scope="col" className="px-3 py-2">{t('wholesale.tableProduct')}</th>
                <th scope="col" className="px-3 py-2">{t('productDetail.volume')}</th>
                <th scope="col" className="px-3 py-2">{t('wholesale.tableMoq')}</th>
                <th scope="col" className="px-3 py-2">{t('wholesale.tablePrice')}</th>
                <th scope="col" className="px-3 py-2">{t('wholesale.tableTiers')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {products.map((p) => {
                const sku = p.variants.flatMap((v) => v.skus).filter((s) => s.is_active)[0]
                return (
                  <tr key={p.id}>
                    <td className="px-3 py-2"><Link to={`/products/${p.slug}`} className="text-brand underline">{p.name}</Link></td>
                    <td className="px-3 py-2">{t('catalog.ml', { n: p.volume_ml })}</td>
                    <td className="px-3 py-2">{p.min_order_quantity || 1}</td>
                    <td className="px-3 py-2">{sku ? `${sku.currency} ${Number(sku.retail_price).toFixed(2)}` : '—'}</td>
                    <td className="px-3 py-2">
                      {sku && sku.quantity_tiers?.length > 0
                        ? sku.quantity_tiers.map((tier) => `${tier.min_quantity}+: ${Number(tier.price).toFixed(2)}`).join(' · ')
                        : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {products.length > 0 && (
        <div className="mb-10">
          <h2 className="text-xl font-semibold mb-4">{t('wholesale.availableProducts')}</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {products.map((p) => <ProductCard key={p.id} product={p} />)}
          </div>
          <p className="mt-4"><Link to="/shop" className="text-brand underline">{t('wholesale.seeFullCatalogue')}</Link></p>
        </div>
      )}

      <div className="max-w-lg border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">{t('wholesale.formTitle')}</h2>
        <InquiryForm defaultType="wholesale" lockType ctaKey="wholesale.cta" />
      </div>
    </div>
  )
}
