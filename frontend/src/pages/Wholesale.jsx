import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import { listProducts } from '../api/products'
import ProductCard from '../components/product/ProductCard'
import InquiryForm from '../components/forms/InquiryForm'

export default function Wholesale() {
  const { locale, t } = useLocale()
  const { cart } = useCart()
  const currency = cart?.currency
  const [products, setProducts] = useState([])

  useEffect(() => {
    listProducts(locale, currency).then(setProducts).catch(() => {})
  }, [locale, currency])

  const benefits = ['wholesale.benefit1', 'wholesale.benefit2', 'wholesale.benefit3', 'wholesale.benefit4']

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
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
        <div className="mb-10">
          <h2 className="text-xl font-semibold mb-4">{t('wholesale.availableProducts')}</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {products.map((p) => <ProductCard key={p.id} product={p} />)}
          </div>
        </div>
      )}

      <div className="max-w-lg border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">{t('wholesale.formTitle')}</h2>
        <InquiryForm defaultType="wholesale" lockType ctaKey="wholesale.cta" />
      </div>
    </div>
  )
}
