import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import * as cartApi from '../api/cart'

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const [cart, setCart] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = useCallback(async (opts) => {
    setLoading(true)
    setError(null)
    try {
      const data = await cartApi.getCart(opts)
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

  const setCurrency = useCallback(async (currency) => {
    const data = await cartApi.setCartCurrency(currency)
    setCart(data)
    return data
  }, [])

  return (
    <CartContext.Provider
      value={{ cart, loading, error, refresh, addItem, updateItem, removeItem, setCurrency }}
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
