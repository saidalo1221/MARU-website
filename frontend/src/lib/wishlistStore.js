import { useEffect, useSyncExternalStore } from 'react'
import { addToWishlist, getWishlist, removeFromWishlist } from '../api/wishlist'

// One shared copy of the signed-in customer's wishlist SKU ids, so every
// product card can show its heart without each card fetching the wishlist.
let skuIds = new Set()
let loaded = false
let loading = false
const listeners = new Set()

function emit() {
  skuIds = new Set(skuIds)
  listeners.forEach((listener) => listener())
}

function subscribe(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function load() {
  if (loaded || loading) return
  loading = true
  getWishlist()
    .then((items) => {
      skuIds = new Set(items.map((i) => i.sku_id))
      loaded = true
      emit()
    })
    .catch(() => {})
    .finally(() => {
      loading = false
    })
}

// Call after a wishlist change made elsewhere (product page, wishlist page).
export function markWishlist(skuId, on) {
  if (on) skuIds.add(skuId)
  else skuIds.delete(skuId)
  emit()
}

export async function toggleWishlist(skuId) {
  if (skuIds.has(skuId)) {
    await removeFromWishlist(skuId)
    markWishlist(skuId, false)
  } else {
    await addToWishlist(skuId)
    markWishlist(skuId, true)
  }
}

// Returns the Set of wishlisted SKU ids; loads it once for a signed-in user.
export function useWishlistSkus(user) {
  const ids = useSyncExternalStore(subscribe, () => skuIds)
  useEffect(() => {
    if (user) {
      load()
    } else if (loaded) {
      loaded = false
      skuIds = new Set()
      emit()
    }
  }, [user])
  return ids
}
