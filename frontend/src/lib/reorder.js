// "Order again" (PRD ТЗ№2 §43 repeat purchase): puts the lines of a past order
// back into the cart. Lines whose SKU no longer exists, or that cannot be added
// (e.g. out of stock), are skipped and counted so the page can say so.
export async function reorder(order, addItem) {
  let added = 0
  let skipped = 0
  for (const item of order.items) {
    if (!item.sku_id) {
      skipped += 1
      continue
    }
    try {
      await addItem(item.sku_id, item.quantity)
      added += 1
    } catch {
      skipped += 1
    }
  }
  return { added, skipped }
}
