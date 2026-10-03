# MARU design system

Implements PRD TZ№2 §45-47, §58, §60-61. Everything visual is driven by tokens, so a new
brand book is a one-file change.

## Tokens - `frontend/src/styles/tokens.css`
Colours (RGB triplets so opacity works: `bg-brand/10`), typography scale (h1, h2, h3, body,
small, caption, button, label), spacing, radius, shadows, border width, layout grid and
animation durations. `frontend/tailwind.config.js` reads these variables; components use the
Tailwind classes (`bg-brand`, `text-h2`, `rounded-token`, `duration-fast`, ...).

- **Brand colours are temporary placeholders.** PRD §45.2 forbids inventing brand colours
  before a brand book exists. When it arrives, change `--color-brand`, `--color-brand-dark`
  and `--color-brand-light` in `tokens.css` - nothing else.
- Dark mode is a set of overrides in `index.css` (`.dark ...`); new components should use the
  existing grey/white/status utility classes so they pick it up.
- A global `:focus-visible` ring and `prefers-reduced-motion` handling are in `tokens.css`.

## Breakpoints (PRD §51)
Mobile 320-767 (default), tablet `md` 768, desktop `lg` 1024, large desktop `2xl` 1440.
Mobile first; no horizontal overflow.

## Components - `frontend/src/components/ui/`
| Component | States / notes |
| --- | --- |
| `Button` | primary, secondary, tertiary, danger; hover, active, focus, loading (`aria-busy`), disabled |
| `FormField` | label, helper, error (`role=alert`, `aria-invalid`), success, disabled |
| `Alert` | info, success, warning, error (error is announced immediately) |
| `Toast` | `ToastProvider` + `useToast()`; polite live region, 4 s |
| `Tabs` | `role=tablist`, arrow-key navigation |
| `Pagination` | previous / next with "Page n of m" |
| `Rating` | stars with a text alternative |

Other shared components: `Breadcrumbs`, `FaqItem` (accordion), `NavMenu` (header dropdown),
`ProductCard` (price, old price, discount, rating, add to cart, quick view, wishlist),
`QuickViewModal` (modal), `MobileMenu` (drawer), `CountrySwitcher`, `LanguageSwitcher`,
`CurrencySwitcher`, `SearchBar` (combobox), `ProductGallery`, `QuantitySelector`,
`VariantSelector`, `ErrorBoundary`.

## States
- **Loading**: skeletons for product grids and the product page; spinner on loading buttons.
- **Empty**: cart, wishlist, orders, search, catalog all explain what happened and offer a next step.
- **Error**: `errorMessage()` never shows server (5xx) text or HTML; `ErrorBoundary` shows
  "Something went wrong. Please try again." with a Try Again button.
- **Success**: order confirmation, payment successful, profile saved, newsletter confirmed.

## Not done
- No Figma file: the PRD's Figma structure (§59) is a designer deliverable.
- "No notifications" empty state: the storefront has no notifications feature.
