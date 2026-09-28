// No server-side search endpoint exists yet; this filters/ranks the
// (currently small) active product list client-side. Replace with a real
// search endpoint once the catalog grows past a few hundred SKUs.
// Shared by SearchResults.jsx (results page) and SearchBar.jsx (typeahead).

function haystackOf(product) {
  return [
    product.name,
    product.slug,
    String(product.volume_ml),
    ...product.variants.flatMap((v) => [v.name, v.color, ...v.skus.map((s) => s.sku_code)]),
  ]
    .join(' ')
    .toLowerCase()
}

// Higher score = more relevant. -1 means "doesn't match at all". Ranks an
// exact/prefix/substring match on the product name above a match that only
// hit a secondary field (slug, SKU code, variant color, ...), the same way
// a search engine favors a title match over a body match.
function scoreProduct(product, query) {
  const name = product.name.toLowerCase()
  const terms = query.split(/\s+/).filter(Boolean)
  if (terms.length === 0) return -1

  const haystack = haystackOf(product)
  if (!terms.every((term) => haystack.includes(term))) return -1

  let score = 0
  if (name === query) score += 100
  else if (name.startsWith(query)) score += 60
  else if (name.includes(query)) score += 40
  terms.forEach((term) => {
    if (name.includes(term)) score += 5
  })
  return score
}

export function rankProducts(products, rawQuery) {
  const query = rawQuery.trim().toLowerCase()
  if (!query) return products
  return products
    .map((p) => ({ p, score: scoreProduct(p, query) }))
    .filter(({ score }) => score >= 0)
    .sort((a, b) => b.score - a.score)
    .map(({ p }) => p)
}
