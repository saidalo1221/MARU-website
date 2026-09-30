import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import * as cartApi from '../api/cart'

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const [cart, setCart] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // A promo code applied on the Cart page must survive later refresh() calls
  // (e.g. Checkout re-pricing when the buyer picks a country/delivery
  // method) or the discount silently disappears once checkout is reached.
  // Kept in a ref rather than state so refresh's identity stays stable.
  const promoCodeRef = useRef(null)

  const refresh = useCallback(async (opts = {}) => {
    if ('promoCode' in opts) promoCodeRef.current = opts.promoCode || null
    setLoading(true)
    setError(null)
    try {
      const data = await cartApi.getCart({ ...opts, promoCode: promoCodeRef.current })
      setCart(data)
      return data
    } catch (err) {
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const addItem = useCallback(async (skuId, quantity) => {
    const data = await cartApi.addCartItem(skuId, quantity)
    setCart(data)
    return data
  }, [])

  const updateItem = useCallback(async (skuId, quantity) => {
    const data = await cartApi.updateCartItem(skuId, quantity)
    setCart(data)
    return data
  }, [])

  const removeItem = useCallback(async (skuId) => {
    const data = await cartApi.removeCartItem(skuId)
    setCart(data)
    return data
  }, [])

  const saveForLater = useCallback(async (skuId) => {
    const data = await cartApi.saveCartItemForLater(skuId)
    setCart(data)
    return data
  }, [])

  const moveToCart = useCallback(async (skuId) => {
    const data = await cartApi.moveSavedItemToCart(skuId)
    setCart(data)
    return data
  }, [])

  const setCurrency = useCallback(async (currency) => {
    const data = await cartApi.setCartCurrency(currency)
    setCart(data)
    return data
  }, [])

  return (
    <CartContext.Provider
      value={{ cart, loading, error, refresh, addItem, updateItem, removeItem, saveForLater, moveToCart, setCurrency }}
    >
      {children}
    </CartContext.Provider>
  )
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used within CartProvider')
  return ctx
}
