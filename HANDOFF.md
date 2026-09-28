# MARU — Session Handoff

Written 2026-09-28 to let a fresh session pick up without re-deriving context.
Read this file first. `TODO.md` and `session_notes.md` are older and predate
everything below (blog, site settings, admin 2FA, uploads, etc.) — don't
trust their "what's done" sections over this one; `PRD.md` is still the
canonical spec.

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
seem to take effect, check for that line; if missing, hard-kill and restart.

**dev.db** already has seed data (2 products, blog posts, about sections,
site settings, a few test users/addresses) accumulated across sessions.
`app/dev_seed.py` documents how to seed a *fresh* SQLite file from scratch,
but running it against the existing `dev.db` will hit unique-constraint
conflicts — don't.

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
PK stays NULL on insert) — this bit me once this session; recreate the table
if it happens.

## Test accounts in dev.db

| Email | Password | Role |
|---|---|---|
| `testuser1@example.com` | `TestPass123!` | super_admin |
| `saidalo497@gmail.com` | (user's own, set at registration) | super_admin — **this is the real intended admin account** |
| `saidalo2020@gmail.com` | (user's own) | product_manager (promoted during testing, otherwise a normal customer) |

## Admin access now requires 2-step email login

`/admin` (frontend) and every `/admin/*` backend endpoint require, on top of
a normal password login, a 6-digit code emailed to the account
(`POST /auth/admin/login` → `POST /auth/admin/verify`, valid ~12h after
verify, enforced inside `require_role()` in `app/dependencies.py`).

**SMTP is not configured** — codes are just logged by `EmailNotifier`
(`Email not sent (SMTP not configured): ... -> email`), not actually
emailed. To get a pending code for testing without real email:
```python
# find it
from app.database import SessionLocal
from app.models.user import User
from app.models.admin_login_code import AdminLoginCode
db = SessionLocal()
u = db.query(User).filter(User.email=='...').first()
row = db.query(AdminLoginCode).filter(AdminLoginCode.user_id==u.id).order_by(AdminLoginCode.id.desc()).first()
print(row.code_hash, row.expires_at)
```
```python
# brute-force the 6-digit code from its sha256 hash (fine — dev only, hash space is tiny)
import hashlib
target = row.code_hash
for i in range(1_000_000):
    if hashlib.sha256(f'{i:06d}'.encode()).hexdigest() == target:
        print(f'{i:06d}'); break
```
To actually send real emails: set `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/
`SMTP_PASSWORD` (Gmail needs an **App Password**, not the real password)/
`SMTP_FROM_EMAIL` in `.env`. Not done yet — user's choice, still pending.

New admins are added via the "Admins" admin page (Super Admin only),
promoting an *existing registered account* by email — it doesn't create
new accounts.

## Feature work done since the "Initial commit" (`ca66c2d`)

Commits, newest first, each with a one-line summary of what to expect if you
open the diff:

- `aa87d65` — promo code was silently dropped between Cart and Checkout
  (`CartContext` now remembers the applied code across refreshes; order
  payload now actually includes it); Shape/Purpose/Country-of-origin are now
  per-locale translatable on products; Orders/Addresses duplicated into the
  header nav next to Shop; Wishlist icon next to Cart icon.
- `bc6e0a2` — checkout now requires login (redirects to `/login?next=...`);
  admin product list/detail show a "visible in shop" indicator + explain why
  a product with no variant/SKU doesn't appear publicly; "Add Product" form
  gained inline RU/UZ/EN translation fields.
- `15b6d38` — fixed `CurrencySwitcher` (was hardcoded to 5 currencies,
  ignoring admin-configured rates); free-form About-Us sections (add/edit/
  translate/reorder/delete, replacing the old hardcoded 7 sections); saved-
  address picker at checkout; translated delivery method labels; B2B/
  Wholesale/Distributor forms use a real product checklist instead of free
  text; removed a duplicate search bar and added relevance ranking +
  autocomplete to search.
- `79cd044` — admin can upload product photos from disk (`POST
  /admin/uploads/image`, served from `app/static/uploads/` — **local disk,
  no S3/object storage exists yet**, won't survive a stateless redeploy on
  UzCloud); product translations (name/description) previously had no admin
  UI or GET endpoint at all — fixed.
- `20f2fc9` — admin-editable Contact/About/Location content (`SiteSettings`
  model), a Leaflet-based `MapPicker` component (free OpenStreetMap +
  Nominatim, no API key) used for both the business location and customer
  addresses (address book + checkout), and the admin 2-step email login
  system described above with admin add/promote/demote.
- `1aedff2` — Blog feature: categories, posts, per-locale translations,
  public pages, admin CRUD.
- `06d3e18` and earlier — admin panel Phase 1+2, i18n, currency conversion;
  see `TODO.md`'s "what's already done" section for the long-form history
  (still accurate for *that* era, just doesn't cover anything above).

## Known gaps / open decisions (carried forward, still true)

- **MariaDB has never been verified.** Every migration this whole project
  has produced (`app/migration_*.sql`, latest is `migration_2026_session6.sql`)
  and `app/schema_mariadb.sql` (fresh-install version) are SQLite-tested
  only — MariaDB isn't reachable from this dev machine. Re-verify before
  any production deploy.
- **Object storage decision still open** (blocks real invoice/document
  storage per PRD, and means the new image-upload feature is local-disk
  only — flagged above).
- **SMTP not configured** — 2FA codes, password resets, order emails all
  currently just log instead of sending.
- Production server reportedly only has Python 3.9 (see `TODO.md`) — this
  codebase uses 3.10+ union syntax (`X | None`) throughout and will not
  import at all on 3.9. Unresolved.
- Everything else in `TODO.md`'s checklist (payment gateway decisions,
  shipping/SMS/ERP vendor picks, GA4/Meta forwarding, cron scheduling for
  the two background tasks, MFA-mandatory-for-admins policy) is still
  outstanding and untouched by the sessions above.

## Conventions worth knowing before adding more features

- Per-locale translation pattern used everywhere (blog, products, about
  sections, site settings): a base entity holds default-language fields; a
  separate `*Translation` table (unique on `entity_id + locale`) overrides
  fields when `?lang=` is passed. Public routers merge base+translation
  before returning; admin routers expose a `GET .../translations` (list) and
  `PUT .../translations/{locale}` (upsert) pair. Always add the GET — I hit
  the "no way to read translations back for the edit form" bug twice
  (products, then almost repeated it for blog) before making it a habit.
- Admin CRUD pages follow one layout: list + inline create form
  (`AdminXxx.jsx`), and where there's nested detail (variants, translations,
  reordering), an expandable-block pattern (see `AdminProductDetail.jsx`'s
  `VariantBlock`/`SectionBlock` style components).
- `apiRequest()` in `frontend/src/api/client.js` now passes `FormData`
  through untouched (needed for the image upload) — don't reintroduce
  `JSON.stringify` for multipart calls.
- Money formatting/conversion in the admin panel goes through
  `AdminCurrencyContext` + the shared `<Money>` component — don't hand-roll
  currency conversion in a new admin page.
