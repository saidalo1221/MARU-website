import { Route, Routes } from 'react-router-dom'
import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import Home from './pages/Home'
import Catalog from './pages/Catalog'
import ProductDetail from './pages/ProductDetail'
import SearchResults from './pages/SearchResults'
import Cart from './pages/Cart'
import Checkout from './pages/Checkout'
import OrderStatus from './pages/OrderStatus'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import OrdersHistory from './pages/OrdersHistory'
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
import AdminProducts from './pages/admin/AdminProducts'
import AdminCategories from './pages/admin/AdminCategories'
import AdminWarehouses from './pages/admin/AdminWarehouses'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/shop" element={<Catalog />} />
          <Route path="/products/:slug" element={<ProductDetail />} />
          <Route path="/search" element={<SearchResults />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/orders/:orderId" element={<OrderStatus />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/account/orders" element={<OrdersHistory />} />
          <Route path="/account/wishlist" element={<Wishlist />} />
          <Route path="/account/addresses" element={<Addresses />} />
          <Route path="/quote" element={<QuoteRequest />} />
          <Route path="/b2b" element={<B2B />} />
          <Route path="/wholesale" element={<Wholesale />} />
          <Route path="/distributor" element={<Distributor />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/delivery" element={<Delivery />} />
          <Route path="/payment" element={<Payment />} />
          <Route path="/returns" element={<Returns />} />
          <Route path="/faq" element={<FAQ />} />
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboard />} />
            <Route path="orders" element={<AdminOrders />} />
            <Route path="orders/:orderId" element={<AdminOrderDetail />} />
            <Route path="quotes" element={<AdminQuotes />} />
            <Route path="quotes/:quoteId" element={<AdminQuoteDetail />} />
            <Route path="reviews" element={<AdminReviews />} />
            <Route path="products" element={<AdminProducts />} />
            <Route path="categories" element={<AdminCategories />} />
            <Route path="warehouses" element={<AdminWarehouses />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
