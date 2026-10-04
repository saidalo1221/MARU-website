// Client-side search over the (currently small) active product list; replace
// with a server endpoint once the catalog grows past a few hundred SKUs.
// Shared by SearchResults.jsx (results page) and SearchBar.jsx (typeahead).
//
// Matching (PRD ТЗ№2 §18): product name, slug, size, variant and colour, SKU
// code, with typo tolerance - a query word may be one or two letters off a
// word of the product ("contaner" finds "container").

const WORD_SPLIT = /[^\p{L}\p{N}]+/u

function wordsOf(text) {
  return String(text).toLowerCase().split(WORD_SPLIT).filter(Boolean)
}

function productWords(product) {
  return [
    ...wordsOf(product.name),
    ...wordsOf(product.slug),
    String(product.volume_ml),
    ...product.variants.flatMap((v) => [...wordsOf(v.name), ...wordsOf(v.color), ...v.skus.flatMap((s) => wordsOf(s.sku_code))]),
  ]
}

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

// Levenshtein distance, giving up (returning max + 1) as soon as it must exceed `max`.
export function editDistance(a, b, max) {
  if (Math.abs(a.length - b.length) > max) return max + 1
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i)
  for (let i = 1; i <= a.length; i += 1) {
    const cur = [i]
    let rowMin = i
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
      if (cur[j] < rowMin) rowMin = cur[j]
    }
    if (rowMin > max) return max + 1
    prev = cur
  }
  return prev[b.length]
}

// How many typos are tolerated for a word of this length (short words: none).
function allowedTypos(length) {
  if (length <= 3) return 0
  return length <= 6 ? 1 : 2
}

function fuzzyHit(term, words) {
  const max = allowedTypos(term.length)
  if (max === 0) return false
  return words.some((w) => {
    if (Math.abs(w.length - term.length) > max) return false
    return editDistance(term, w, max) <= max || (w.length > term.length && editDistance(term, w.slice(0, term.length), max) <= max)
  })
}

// Higher score = more relevant. null means "doesn't match at all". A name match
// ranks above a match on a secondary field, and an exact match above a typo match.
function scoreProduct(product, query) {
  const name = product.name.toLowerCase()
  const terms = query.split(/\s+/).filter(Boolean)
  if (terms.length === 0) return null

  const haystack = haystackOf(product)
  const words = productWords(product)
  let fuzzy = 0
  for (const term of terms) {
    if (haystack.includes(term)) continue
    if (fuzzyHit(term, words)) fuzzy += 1
    else return null
  }

  let score = 0
  if (name === query) score += 100
  else if (name.startsWith(query)) score += 60
  else if (name.includes(query)) score += 40
  terms.forEach((term) => {
    if (name.includes(term)) score += 5
  })
  return score - fuzzy * 3
}

export function rankProducts(products, rawQuery) {
  const query = rawQuery.trim().toLowerCase()
  if (!query) return products
  return products
    .map((p) => ({ p, score: scoreProduct(p, query) }))
    .filter(({ score }) => score !== null)
    .sort((a, b) => b.score - a.score)
    .map(({ p }) => p)
}

// Categories whose name matches the query (typo tolerant), for the typeahead.
export function matchCategories(categories, rawQuery) {
  const query = rawQuery.trim().toLowerCase()
  if (!query) return []
  const terms = query.split(/\s+/).filter(Boolean)
  return categories.filter((c) => {
    const name = c.name.toLowerCase()
    const words = wordsOf(c.name)
    return terms.every((term) => name.includes(term) || fuzzyHit(term, words))
  })
}
