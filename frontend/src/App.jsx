import { Route, Routes } from 'react-router-dom'
import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import EmailVerifyBanner from './components/layout/EmailVerifyBanner'
import CountryBanner from './components/layout/CountryBanner'
import ConsentBanner from './components/layout/ConsentBanner'
import Home from './pages/Home'
import Catalog from './pages/Catalog'
import ProductDetail from './pages/ProductDetail'
import BlogHome from './pages/BlogHome'
import BlogArticle from './pages/BlogArticle'
import SearchResults from './pages/SearchResults'
import Cart from './pages/Cart'
import Checkout from './pages/Checkout'
import OrderStatus from './pages/OrderStatus'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import VerifyEmail from './pages/VerifyEmail'
import OrdersHistory from './pages/OrdersHistory'
import TrackOrder from './pages/TrackOrder'
import NewsletterAction from './pages/NewsletterAction'
import AccountPrivacy from './pages/AccountPrivacy'
import LegalPage from './pages/LegalPage'
import AdminNewsletter from './pages/admin/AdminNewsletter'
import Wishlist from './pages/Wishlist'
import Addresses from './pages/Addresses'
import QuoteRequest from './pages/QuoteRequest'
import B2B from './pages/B2B'
import Wholesale from './pages/Wholesale'
import Distributor from './pages/Distributor'
import About from './pages/About'
import Contact from './pages/Contact'
import Delivery from './pages/Delivery'
import Payment from './pages/Payment'
import Returns from './pages/Returns'
import FAQ from './pages/FAQ'
import AdminLayout from './pages/admin/AdminLayout'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminOrders from './pages/admin/AdminOrders'
import AdminOrderDetail from './pages/admin/AdminOrderDetail'
import AdminQuotes from './pages/admin/AdminQuotes'
import AdminQuoteDetail from './pages/admin/AdminQuoteDetail'
import AdminReviews from './pages/admin/AdminReviews'
import AdminBlogPosts from './pages/admin/AdminBlogPosts'
import AdminBlogPostDetail from './pages/admin/AdminBlogPostDetail'
import AdminBlogCategories from './pages/admin/AdminBlogCategories'
import AdminSiteSettings from './pages/admin/AdminSiteSettings'
import AdminAboutSections from './pages/admin/AdminAboutSections'
import AdminPageSections from './pages/admin/AdminPageSections'
import AdminAdmins from './pages/admin/AdminAdmins'
import AdminProducts from './pages/admin/AdminProducts'
import AdminProductDetail from './pages/admin/AdminProductDetail'
import AdminCategories from './pages/admin/AdminCategories'
import AdminWarehouses from './pages/admin/AdminWarehouses'
import AdminPromoCodes from './pages/admin/AdminPromoCodes'
import AdminShippingRates from './pages/admin/AdminShippingRates'
import AdminTaxRules from './pages/admin/AdminTaxRules'
import AdminExchangeRates from './pages/admin/AdminExchangeRates'
import AdminNotificationTemplates from './pages/admin/AdminNotificationTemplates'
import AdminIntegrationLogs from './pages/admin/AdminIntegrationLogs'
import AdminAuditLog from './pages/admin/AdminAuditLog'
import AdminAnalyticsEvents from './pages/admin/AdminAnalyticsEvents'
import AccountDashboard from './pages/AccountDashboard'
import CategoryPage from './pages/CategoryPage'
import AccountProfile from './pages/AccountProfile'
import ContentPage from './pages/ContentPage'
import NotFound from './pages/NotFound'
import { useLocale } from './context/LocaleContext'

export default function App() {
  const { t } = useLocale()
  return (
    <div className="min-h-screen flex flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[70] focus:top-2 focus:left-2 focus:bg-white focus:text-brand focus:px-3 focus:py-2 focus:rounded focus:shadow"
      >
        {t('common.skipToContent')}
      </a>
      <Header />
      <CountryBanner />
      <ConsentBanner />
      <EmailVerifyBanner />
      <main id="main" tabIndex={-1} className="flex-1 focus:outline-none">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/shop" element={<Catalog />} />
          <Route path="/products/:slug" element={<ProductDetail />} />
          <Route path="/blog" element={<BlogHome />} />
          <Route path="/blog/:slug" element={<BlogArticle />} />
          <Route path="/search" element={<SearchResults />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/orders/:orderId" element={<OrderStatus />} />
          <Route path="/track" element={<TrackOrder />} />
          <Route path="/newsletter/:action" element={<NewsletterAction />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/shop/:slug" element={<CategoryPage />} />
          <Route path="/account" element={<AccountDashboard />} />
          <Route path="/account/profile" element={<AccountProfile />} />
          <Route path="/account/orders" element={<OrdersHistory />} />
          <Route path="/account/wishlist" element={<Wishlist />} />
          <Route path="/account/addresses" element={<Addresses />} />
          <Route path="/account/privacy" element={<AccountPrivacy />} />
          <Route path="/quote" element={<QuoteRequest />} />
          <Route path="/b2b" element={<B2B />} />
          <Route path="/wholesale" element={<Wholesale />} />
          <Route path="/distributor" element={<Distributor />} />
          <Route path="/about" element={<About />} />
          <Route path="/manufacturing" element={<ContentPage pageKey="manufacturing" />} />
          <Route path="/quality" element={<ContentPage pageKey="quality" />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/delivery" element={<Delivery />} />
          <Route path="/payment" element={<Payment />} />
          <Route path="/returns" element={<Returns />} />
          <Route path="/faq" element={<FAQ />} />
          <Route path="/privacy" element={<LegalPage pageKey="privacy" />} />
          <Route path="/terms" element={<LegalPage pageKey="terms" />} />
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboard />} />
            <Route path="orders" element={<AdminOrders />} />
            <Route path="orders/:orderId" element={<AdminOrderDetail />} />
            <Route path="quotes" element={<AdminQuotes />} />
            <Route path="quotes/:quoteId" element={<AdminQuoteDetail />} />
            <Route path="reviews" element={<AdminReviews />} />
            <Route path="blog/posts" element={<AdminBlogPosts />} />
            <Route path="blog/posts/:postId" element={<AdminBlogPostDetail />} />
            <Route path="blog/categories" element={<AdminBlogCategories />} />
            <Route path="site-settings" element={<AdminSiteSettings />} />
            <Route path="about-sections" element={<AdminAboutSections />} />
            <Route path="page-sections" element={<AdminPageSections />} />
            <Route path="admins" element={<AdminAdmins />} />
            <Route path="products" element={<AdminProducts />} />
            <Route path="products/:productId" element={<AdminProductDetail />} />
            <Route path="categories" element={<AdminCategories />} />
            <Route path="warehouses" element={<AdminWarehouses />} />
            <Route path="promo-codes" element={<AdminPromoCodes />} />
            <Route path="shipping-rates" element={<AdminShippingRates />} />
            <Route path="tax-rules" element={<AdminTaxRules />} />
            <Route path="exchange-rates" element={<AdminExchangeRates />} />
            <Route path="notification-templates" element={<AdminNotificationTemplates />} />
            <Route path="integration-logs" element={<AdminIntegrationLogs />} />
            <Route path="audit-log" element={<AdminAuditLog />} />
            <Route path="analytics-events" element={<AdminAnalyticsEvents />} />
            <Route path="newsletter" element={<AdminNewsletter />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
