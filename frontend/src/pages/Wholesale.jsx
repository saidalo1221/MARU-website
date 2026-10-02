import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import { listProducts } from '../api/products'
import ProductCard from '../components/product/ProductCard'
import InquiryForm from '../components/forms/InquiryForm'
import PageIntro from '../components/layout/PageIntro'
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
  const terms = [
    ['wholesale.moqTitle', 'wholesale.moqText'],
    ['wholesale.packagingTitle', 'wholesale.packagingText'],
    ['wholesale.pricingTitle', 'wholesale.pricingText'],
    ['productDetail.delivery', 'wholesale.deliveryText'],
  ]

  return (
    <div className="max-w-5xl mx-auto px-4 py-12 md:py-16">
      <Seo title={t('wholesale.title')} description={t('wholesale.subtitle')} />
      <PageIntro title={t('wholesale.title')} subtitle={t('wholesale.subtitle')} />

      <ul className="mb-12 grid gap-4 sm:grid-cols-2">
        {benefits.map((key, i) => (
          <li key={key} className={`rounded-3xl p-6 md:p-8 ${i === 0 ? 'bg-brand text-white' : i === 3 ? 'bg-brand-light' : 'border border-gray-200 bg-gray-50'}`}>
            {t(key)}
          </li>
        ))}
      </ul>

      <dl className="mb-12 grid gap-6 rounded-3xl border border-gray-200 bg-gray-50 p-6 sm:grid-cols-2 md:p-8">
        {terms.map(([titleKey, textKey]) => (
          <div key={titleKey}>
            <dt className="mb-1 font-semibold">{t(titleKey)}</dt>
            <dd className="text-gray-600">{t(textKey)}</dd>
          </div>
        ))}
      </dl>

      {products.length > 0 && (
        <div className="mb-12">
          <h2 className="mb-4 text-2xl font-semibold tracking-tight">{t('wholesale.tableTitle')}</h2>
          <div className="overflow-x-auto rounded-3xl border border-gray-200">
            <table className="w-full text-sm">
              <thead className="bg-brand-light text-left">
                <tr>
                  <th scope="col" className="px-4 py-3">{t('wholesale.tableProduct')}</th>
                  <th scope="col" className="px-4 py-3">{t('productDetail.volume')}</th>
                  <th scope="col" className="px-4 py-3">{t('wholesale.tableMoq')}</th>
                  <th scope="col" className="px-4 py-3">{t('wholesale.tablePrice')}</th>
                  <th scope="col" className="px-4 py-3">{t('wholesale.tableTiers')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {products.map((p) => {
                  const sku = p.variants.flatMap((v) => v.skus).filter((s) => s.is_active)[0]
                  return (
                    <tr key={p.id}>
                      <td className="px-4 py-3"><Link to={`/products/${p.slug}`} className="text-brand underline">{p.name}</Link></td>
                      <td className="px-4 py-3">{t('catalog.ml', { n: p.volume_ml })}</td>
                      <td className="px-4 py-3">{p.min_order_quantity || 1}</td>
                      <td className="px-4 py-3">{sku ? `${sku.currency} ${Number(sku.retail_price).toFixed(2)}` : '-'}</td>
                      <td className="px-4 py-3">
                        {sku && sku.quantity_tiers?.length > 0
                          ? sku.quantity_tiers.map((tier) => `${tier.min_quantity}+: ${Number(tier.price).toFixed(2)}`).join(' · ')
                          : '-'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {products.length > 0 && (
        <div className="mb-12">
          <h2 className="mb-5 text-2xl font-semibold tracking-tight">{t('wholesale.availableProducts')}</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {products.map((p) => <ProductCard key={p.id} product={p} />)}
          </div>
          <p className="mt-5"><Link to="/shop" className="text-brand underline">{t('wholesale.seeFullCatalogue')}</Link></p>
        </div>
      )}

      <div className="mx-auto max-w-xl rounded-3xl border border-gray-200 bg-gray-50 p-6 md:p-8">
        <h2 className="mb-5 text-xl font-semibold">{t('wholesale.formTitle')}</h2>
        <InquiryForm defaultType="wholesale" lockType ctaKey="wholesale.cta" />
      </div>
    </div>
  )
}
