// Run with: node tests/search.test.mjs  (no test runner is installed in this project)
import { rankProducts, matchCategories, editDistance } from '../src/lib/search.js'
const mk = (id, name, slug, ml, color, sku) => ({ id, name, slug, volume_ml: ml, variants: [{ name: color, color, skus: [{ sku_code: sku }] }] })
const products = [
  mk(1, 'MARU Round Container', 'maru-round-container', 350, 'Clear', 'SKU-350-CLR'),
  mk(2, 'MARU Rectangular Container', 'maru-rect-container', 1000, 'White', 'SKU-1000-WHT'),
  mk(3, 'Круглый контейнер MARU', 'maru-kruglyj', 800, 'Прозрачный', 'SKU-800-CLR'),
]
const names = (q) => rankProducts(products, q).map((p) => p.id).join(',') || '-'
const checks = [
  ['exact name', names('round'), '1'],
  ['typo contaner', names('contaner'), '1,2'],
  ['typo rectangluar', names('rectangluar'), '2'],
  ['size 1000', names('1000'), '2'],
  ['sku code', names('sku-350'), '1'],
  ['cyrillic typo', names('контэйнер'), '3'],
  ['color', names('white'), '2'],
  ['short word no fuzzy', names('rou'), '1'],
  ['nonsense', names('zzzzqq'), '-'],
  ['distance', String(editDistance('kitten', 'sitting', 5)), '3'],
  ['category typo', matchCategories([{ name: 'Containers' }, { name: 'Lids' }], 'contaners').map((c) => c.name).join(','), 'Containers'],
]
let bad = 0
for (const [label, got, want] of checks) {
  const ok = got === want
  if (!ok) bad += 1
  console.log(ok ? 'ok  ' : 'FAIL', label, '=>', got, ok ? '' : `(wanted ${want})`)
}
process.exit(bad ? 1 : 0)
