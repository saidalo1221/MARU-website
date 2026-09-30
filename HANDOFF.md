# MARU — Session Handoff

Written 2026-09-28, updated 2026-09-30, to let a fresh session pick up without
re-deriving context or re-reading the whole diff history. Read this file
first. `TODO.md` and `session_notes.md` are older and predate everything
below — don't trust their "what's done" sections over this one. `PRD.md` is
still the canonical spec; a full PRD-vs-codebase gap audit was done this
session (see "PRD gap audit" below) and is the current source of truth for
what's missing.

## What this project is

MARU: a plastic-food-container e-commerce site. FastAPI + SQLAlchemy +
MariaDB backend, React + Tailwind frontend, hosted target is UzCloud.
`CLAUDE.md` has the house rules (verify before editing, smallest correct
change, no unnecessary abstraction) — read it before making changes.

## Running it locally

Backend **must** override `DATABASE_URL` or it silently falls through to
`.env`'s real (unreachable-from-here) MariaDB URL and every DB endpoint
500s with a generic error:

```
cd "C:\Users\user\Desktop\best one yet"
DATABASE_URL=sqlite:///dev.db python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:
```
cd "C:\Users\user\Desktop\best one yet\frontend"
npm run dev   # http://localhost:5173, backend expected at 127.0.0.1:8000
```

**Known uvicorn gotcha**: `--reload` sometimes logs "Reloading..." but never
spawns a new worker (no "Started server process" line). If a fix doesn't
seem to take effect, check for that line in the log; if it's missing,
hard-kill the process tree (`taskkill //F //T //PID <reloader pid>`) and
restart — a plain re-request won't fix it.

**dev.db** already has seed data (2 products, blog posts, about sections,
page sections, site settings, a few test users/addresses/warehouses)
accumulated across sessions. `app/dev_seed.py` documents how to seed a
*fresh* SQLite file from scratch, but running it against the existing
`dev.db` will hit unique-constraint conflicts — don't. `PAGE_SECTIONS` and
`ABOUT_SECTIONS` constants in `dev_seed.py` are also reused directly by
one-off backfill scripts when seeding just those tables into an
already-seeded `dev.db` — see git history around commit `758d98a` for the
pattern if you need to do this again for a new table.

If you add a new SQLAlchemy model and need its table in `dev.db`, `create_all()`
alone won't apply the SQLite BigInteger-as-INTEGER-autoincrement patch that
`dev_seed.py` applies at import time. Pattern that works:
```python
import app.dev_seed  # applies the patch as a side effect of importing
from app.database import engine
from app.models.your_model import YourModel
YourModel.__table__.create(bind=engine, checkfirst=True)
```
Creating the table without that patch silently breaks autoincrement (BIGINT
PK stays NULL on insert) — recreate the table if it happens.

## Test accounts in dev.db

| Email | Password | Role |
|---|---|---|
| `testuser1@example.com` | `TestPass123!` | super_admin |
| `saidalo497@gmail.com` | (user's own, set at registration) | super_admin — **this is the real intended admin account** |
| `saidalo2020@gmail.com` | (user's own) | product_manager (promoted during testing, otherwise a normal customer) |

## Email (SMTP) — now actually configured and working

`.env`'s `SMTP_*` are filled in (Gmail, `smtp.gmail.com:587`, an app
password) and verified with real sends this session. All four
`EmailNotifier` paths work for real: admin 2FA codes, customer new-device
login codes, password reset, email verification. Caveat: personal Gmail
caps ~500 recipients/day and isn't great for deliverability/branding at
real volume — swap `SMTP_*` to a real transactional provider
(SendGrid/Mailgun/SES) before production launch; no code changes needed to
swap providers.

**If SMTP ever looks broken again** (codes not arriving): the #1 cause this
session was a *stale backend process* — env vars are read once at process
startup, so if `.env` changes after the server is already running, it keeps
using the old (blank) SMTP config silently. Hard-restart the backend
whenever you touch `.env`.

If you still need to read a pending code without email (e.g. testing on a
machine with no real inbox access):
```python
from app.database import SessionLocal
from app.models.user import User
from app.models.admin_login_code import AdminLoginCode  # or LoginDeviceCode for customer login
import hashlib
db = SessionLocal()
u = db.query(User).filter(User.email=='...').first()
row = db.query(AdminLoginCode).filter(AdminLoginCode.user_id==u.id).order_by(AdminLoginCode.id.desc()).first()
target = row.code_hash
for i in range(1_000_000):
    if hashlib.sha256(f'{i:06d}'.encode()).hexdigest() == target:
        print(f'{i:06d}'); break
```

## Auth/security — three separate mechanisms, don't confuse them

1. **Admin 2-step email login** (`/auth/admin/login` → `/auth/admin/verify`,
   `app/routers/auth.py`) — required for every non-customer role to reach
   `/admin` or any `/admin/*` endpoint, on top of a normal password login.
   Valid ~12h (`User.admin_mfa_verified_until`), enforced in
   `require_role()` (`app/dependencies.py`). Admin panel also now
   **auto-logs-out after 5 minutes of no mouse/keyboard/touch activity**
   (`AdminAccessGate.jsx`), independent of that 12h window.
2. **Customer new-device email verification** (`/auth/login` →
   `/auth/login/verify-device` when needed) — added this session. A
   browser gets an opaque `device_id` (localStorage, `api/client.js`'s
   `getDeviceId()`) sent with every login attempt. Unrecognized device →
   `/auth/login` returns `{device_verification_required: true}` instead of
   a token, an email code is sent, and the frontend (`Login.jsx`) shows a
   second-step code form. Once verified, the device is remembered
   (`TrustedDevice` table) so this only happens once per browser.
3. **Account lockout** — 5 failed password attempts locks the account for
   15 minutes (`User.failed_login_attempts`/`locked_until`,
   `MAX_FAILED_LOGIN_ATTEMPTS`/`LOCKOUT_MINUTES` in `auth.py`), shared logic
   between customer and admin login.

New admins are added via the "Admins" admin page (Super Admin only),
promoting an *existing registered account* by email — it doesn't create
new accounts.

## Feature work done 2026-09-29/30, newest first

All committed on `main`, nothing pushed. Everything was verified at the level
noted; **none of the UI has been looked at in a real browser yet** (see
"Not yet verified" below).

- `f9ea569` — Loading skeletons (`components/Skeleton.jsx`) on catalog,
  search and product pages (PRD s53). WCAG 2.1 AA fixes from a static audit:
  `<html lang>` now follows the UI language (`LocaleContext`), skip-to-content
  link + focusable `<main id="main">`, `aria-label` on placeholder-only fields
  and unlabeled selects (`PasswordInput` defaults its label to its
  placeholder), storefront `text-gray-400` -> `text-gray-500` for contrast,
  Quick View dialog has an accessible name and initial focus. Admin pages were
  NOT touched by the contrast/label pass.
- `9106902` — Analytics: `remove_from_cart` (only when an item was really
  removed) and `refund` (after a completed refund) now recorded server-side.
- `b2c7f91` — All 21 FAQ Q&A pairs seeded in ru/uz in `app/dev_seed.py`.
  **`dev.db` was also updated, but `dev.db` is gitignored** — a real/staging
  database needs these entered via the admin "Support Pages Content" page.
  The translations are my drafts, not native-speaker reviewed. The one junk
  test translation on the first FAQ row in `dev.db` was overwritten.
- `a31e8cc` — Product gallery: hover-zoom + full-screen lightbox (Esc/arrows),
  inline video. A gallery entry is just a URL, classified in
  `frontend/src/lib/media.js`: `.mp4/.webm` -> `<video>`, YouTube link ->
  embedded iframe, anything else -> image (no schema change). New
  `POST /admin/uploads/video` (mp4/webm, 25MB, local disk like images).
  Mobile catalog filters are now a bottom sheet.
- `85ee617` — Rate limits on cart (router-wide 300/60s), order lookup (30/60s)
  and cancel, wishlist, reviews, addresses, blog/about/page-sections/
  site-settings, shipping, categories, exchange rates, payment methods,
  `auth/me`, `verify-email`. **Payme/Click webhooks are deliberately
  unlimited** (few shared provider IPs, authenticated by signature). No search
  endpoint exists — search filters the product list client-side, covered by
  `products_list`.
- `3c69195` — Committed the previously-uncommitted batch: product badges
  (`app/services/badges.py`, auto/manual per product), multi-image variant
  gallery (`variant_images`), Quick View modal, country auto-detect banner,
  dark mode (`ThemeContext`, retrofit via `.dark` overrides in `index.css`),
  `migration_2026_session8.sql`.
- `9571d47` — Cart upsell: `GET /cart/recommendations` ranks products by
  co-purchase in past paid orders, then best sellers, then newest; excludes
  cart contents and out-of-stock; heading says "Frequently bought together"
  only when the top result really came from order history, else "You may also
  like". Advisory only — frontend swallows any failure so checkout is never
  blocked. `app/services/recommendations.py`.

### Browser verification (done 2026-09-30, Chrome, dark mode, ru locale)

Verified in a real browser: badges match API data; gallery hover-zoom,
lightbox (Esc/arrows/scroll-lock/focus), mp4 playback and YouTube embed;
Quick View; cart upsell (excludes cart items and out-of-stock, honest
"You may also like" heading); mobile filter bottom sheet; country banner
(incl. EUR switch and dismiss); dark-mode toggle; `<html lang>` sync; skip
link; skeleton loading state. Console had no errors.

Bugs found and fixed in `6178908`: the mobile header was 499px wide at 390px
(hamburger off-screen; search now has its own row), the Quick View button was
unreadable in dark mode and overlapped titles (now an in-flow button), the
lightbox image showed tiny, and two close buttons read "Close quick view".

Still NOT verified: admin video-upload UI (needs admin 2FA login; the backend
endpoint itself was tested), light mode visuals, touch behaviour on a real
phone, checkout/account pages at phone width, Safari/Firefox.

Open decision: `CountryBanner` calls `ipapi.co` from the visitor's browser,
which discloses every visitor's IP to a third party with no consent step and
has a low free-tier rate limit. Consider a consent gate or a server-side/paid
geo lookup before launch.

### Gotchas learned this session

- **Rate limits key on `request.client.host`.** Behind a reverse proxy that is
  the proxy's IP, so every visitor would share one bucket and get 429s. Before
  deploying, run uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy>`
  (or equivalent) so the real client IP is used.
- **Windows Python defaults to cp1251** when reading/writing files without an
  explicit encoding. Always pass `encoding="utf-8"` (or work in bytes); a bare
  `open(...)` silently corrupted an em dash into an invalid byte once, and
  console output of Cyrillic prints as `?` — write to a UTF-8 file and read it.
- Most source files have CRLF endings in the working tree; preserve them when
  scripting edits or diffs balloon.
- Background dev servers can be reaped by Claude Code under memory pressure;
  restart them manually (commands in "Running it locally").
- Video/image uploads are local-disk only; same object-storage caveat as before.
- The frontend talks to the backend directly at `VITE_API_BASE_URL` (default
  `http://127.0.0.1:8000/api/v1`); Vite only proxies `/sitemap.xml`. Requesting
  `/api/...` on :5173 returns the SPA's HTML with a 200, so a 200 there proves
  nothing — hit :8000.
- Claude-in-Chrome's `resize_window` did not change the viewport. To test
  phone widths, load the site in a same-origin `<iframe style="width:390px">`
  from a scratch page (e.g. `/robots.txt`) and drive it via `contentDocument`.

## Feature work done 2026-09-28, newest first

- `395ce40` — Per-page SEO: `<Seo>` component (react-helmet-async) sets
  title/description/canonical/OG/Twitter tags + JSON-LD on every public
  page, `noindex` on account/checkout/admin pages. **Gotcha hit and fixed**:
  `<Helmet>`'s default `defer` mode schedules its DOM commit via
  `requestAnimationFrame`, which didn't reliably fire in this dev
  environment — tags silently never updated. Fixed with
  `<Helmet defer={false}>`. Also: `react-helmet-async` never removes a
  static tag it didn't create itself, so `index.html` had to be trimmed to
  just a `<title>` fallback (a static `meta[name=description]` there would
  duplicate forever next to Helmet's). New `GET /sitemap.xml` (root-level,
  not under `/api/v1`, dynamically lists products/blog posts from the DB —
  a prod reverse proxy needs to route `/sitemap.xml` there specifically)
  and `frontend/public/robots.txt`.
- `c6fdbba` — About Us Sections / Support Pages Content admin lists now
  show the section title translated to whatever language the header
  switcher is set to (e.g. "История (History)"), instead of always the
  base English — was a real, reported bug. Editing still targets the base
  fields, so this is display-only. Added currency delete
  (`DELETE /admin/exchange-rates/{id}`).
- `9ea0e14` — Admin "Add Currency" is now a type-to-search picker (search
  by code or name, mirrors the storefront product search) over the FX
  provider's full currency list; picking one auto-fetches the live rate
  instead of typing one in. Sync now refreshes every currency an admin has
  actually added (was hardcoded to 4). `AdminWarehouses` gained a
  `MapPicker` for setting a warehouse's location by clicking a map. Blog
  post cover image gained a "Choose File" upload option (reused
  `/admin/uploads/image`, widened its role gate to include Marketing
  Manager — it was Product-Manager-only before, which 403'd blog uploads).
- `758d98a` — New `PageSection`/`PageSectionTranslation` model (same
  free-form pattern as the pre-existing `AboutSection`) + admin CRUD, so
  Delivery/Payment/Returns/FAQ/Contact page copy is now admin-editable from
  a new "Support Pages Content" admin page — previously hardcoded in the
  i18n dictionary. Seeded with the prior hardcoded copy so this wasn't a
  content regression (FAQ's 21 Q&A pairs seeded English-only — add ru/uz
  via the admin panel when convenient). Admin auto-logout after 5 min idle
  (see Auth section above).
- `836c972` — Account lockout + customer new-device 2FA (see Auth section
  above). New tables: `TrustedDevice`, `LoginDeviceCode`. New `User`
  columns: `failed_login_attempts`, `locked_until`.
- `6ca6b41` — Password show/hide toggle (`PasswordInput.jsx`) on every
  password field. Per-locale blog slugs (`BlogPostTranslation.slug` — falls
  back to the base slug when unset; public lookup tries both). Enlarged the
  wishlist/favorite heart icon.
- `f46ef82` — Fixed a real crash: `AdminDashboard` read `user.email`
  unguarded, and `AdminAccessGate` briefly renders its `children` with a
  stale `phase==='granted'` for one render after `user` goes null (e.g. on
  logout), before its effect resets `phase`. No error boundary → the whole
  tree unmounted to a blank white screen. This was the actual cause behind
  two separate user reports ("logout gives white screen" and "admin logout
  doesn't log out the main site") — they were the same bug.
- `8b73af2` — Frontend for email verification on signup (backend endpoints
  already existed, nothing consumed them): `/verify-email` page, resend
  banner for unverified accounts.
- Also this session, **data fixes** (not in a commit — direct `dev.db`
  edits, not needed on a fresh DB since `dev_seed.py`'s source strings were
  always correct): About Us section and blog post Russian translations
  were stored as mojibake (corrupted encoding) in `dev.db` — re-written
  from `dev_seed.py`'s known-good source strings, matched by stable English
  title/slug rather than position (sections/posts had been reordered via
  the admin UI since seeding, so a naive positional fix would have swapped
  two entries — caught and corrected).

For anything before this session (admin panel, i18n, currency conversion,
blog, site settings, map-based addresses, product uploads, checkout UX),
see the git log — `ca66c2d` is the initial commit merging all of it.

## PRD gap audit (done this session, still current)

A full read of `PRD.md` cross-checked against the actual codebase. Full
detail is in the conversation this was produced in (not saved as a
separate file) — summary:

**Solid / already built**: order state machine, inventory reservation
(race-safe, TTL expiry), payment idempotency, multi-provider payment
adapter pattern (Payme/Click/Stripe/PayPal — real code, just unconfigured,
no live credentials), quantity price tiers, RBAC roles, admin MFA, audit
log, Bitrix24 CRM push, integration logging with retry/backoff.

**Blocked on a vendor/API decision, not effort** — don't build until
decided: ERP/1С integration, SMS/WhatsApp/Telegram notifications, Uzum
marketplace connector, Uzum Pay.

**Actually missing, buildable now** (priority order; items 3-8 of the original list — badges, Quick View, country banner, cart upsell, rate-limit coverage, loading skeletons — are now done, see 2026-09-29/30 above):
1. ~~SEO meta tags / sitemap~~ — **done**.
2. GA4/Meta pixel forwarding — events are captured server-side
   (`app/services/analytics.py`) but never forwarded; needs a Measurement
   Protocol secret.
3. Object storage (S3-compatible) — uploads are local-disk only
   (`app/routers/admin_uploads.py`), breaks on a stateless redeploy,
   blocks real invoice storage.
4. Product badges (New/Sale/Best Seller/Out of Stock) — not in frontend.
5. Quick View on product cards — not built.
6. Country auto-detect banner — not built.
7. "Frequently bought together" / cart upsell — not built.
8. Rate-limit coverage — only ~13 endpoints have it; checkout/payment/
   search should be spot-checked against `app/core/rate_limit.py`'s
   `rate_limit()` dependency.

**Not deeply checked, would need a follow-up pass**: loading-skeleton
consistency, WCAG 2.1 AA accessibility compliance, full analytics-event
coverage against the PRD's event list.

## Known gaps / open decisions (carried forward, still true)

- **MariaDB has never been verified.** Every migration this whole project
  has produced (`app/migration_*.sql`, latest is `migration_2026_session8.sql`)
  and `app/schema_mariadb.sql` (fresh-install version) are SQLite-tested
  only — MariaDB isn't reachable from this dev machine. Re-verify before
  any production deploy. `migration_2026_session7.sql` covers page sections, trusted devices,
  account lockout, blog slugs, warehouse lat/long; `migration_2026_session8.sql`
  covers `variant_images` and the product badge columns.
- **Object storage decision still open** (see PRD gap audit above).
- Production server reportedly only has Python 3.9 (see `TODO.md`) — this
  codebase uses 3.10+ union syntax (`X | None`) throughout and will not
  import at all on 3.9. Unresolved.
- Everything blocked-on-vendor-decision from the PRD audit above (ERP,
  SMS/WhatsApp/Telegram, Uzum marketplace, Uzum Pay) is still outstanding.
- GA4/Meta forwarding is still unbuilt, and so are the **client-side analytics
  events** the PRD lists (`view_item`, `view_item_list`, `search`, `view_cart`,
  `add_payment_info`, `select_variant`): they only happen in the browser, so
  they need a small public, rate-limited, name-whitelisted ingest endpoint
  (e.g. `POST /analytics/events`) plus a frontend tracker. Also `begin_checkout`
  currently fires when the order is *placed*, not when checkout opens.
- Accessibility follow-ups: dialogs have initial focus but no focus trap or
  focus restore; error messages lack `role="alert"`; admin pages weren't
  audited; a real axe/keyboard pass in a browser is still owed.

## Conventions worth knowing before adding more features

- Per-locale translation pattern used everywhere (blog, products, about
  sections, page sections, site settings): a base entity holds
  default-language fields; a separate `*Translation` table (unique on
  `entity_id + locale`) overrides fields when `?lang=` is passed. Public
  routers merge base+translation before returning; admin routers expose a
  `GET .../translations` (list) and `PUT .../translations/{locale}`
  (upsert) pair. Always add the GET. If an admin *list* endpoint needs to
  show translated text for display (not editing), add it as a separate
  `display_title` field built server-side (see `admin_about_sections.py`'s
  `_to_out()`) rather than overwriting the base field in the response —
  otherwise the edit form initializes from translated text and saving it
  back corrupts the base-language source content.
- Admin CRUD pages follow one layout: list + inline create form
  (`AdminXxx.jsx`), and where there's nested detail (variants, translations,
  reordering), an expandable-block pattern (see `AdminProductDetail.jsx`'s
  `VariantBlock`/`SectionBlock`, or `AdminPageSections.jsx` for a
  page-scoped variant with a page-selector tab bar).
- `apiRequest()` in `frontend/src/api/client.js` now passes `FormData`
  through untouched (needed for image uploads) — don't reintroduce
  `JSON.stringify` for multipart calls.
- Money formatting/conversion in the admin panel goes through
  `AdminCurrencyContext` + the shared `<Money>` component — don't hand-roll
  currency conversion in a new admin page. For exchange rates specifically,
  prefer fetching a live rate via `app/services/fx_provider.py`'s
  `fetch_rate_for_currency()` over asking the admin to type one in.
- Every new public page should get a `<Seo>` tag
  (`frontend/src/components/Seo.jsx`) — `noindex` for
  account/checkout/auth pages, real title/description/image for anything
  else. If it's a content type worth rich previews, add a `jsonLd` prop
  (see `ProductDetail.jsx`/`BlogArticle.jsx` for examples).
- When restarting the backend, always hard-kill the process tree (find the
  PID via `netstat -ano | grep 8000`, then `taskkill //F //T //PID <pid>`)
  rather than trusting `--reload` — see the uvicorn gotcha above.
