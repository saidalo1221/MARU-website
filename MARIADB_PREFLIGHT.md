# MariaDB pre-flight (2026-09-30)

Nothing here has been run against a real MariaDB: this machine cannot reach
UzCloud and has no MariaDB server. Static checks only.

## What was checked statically
- Compiled all 47 SQLAlchemy models with the MySQL dialect and compared them
  with `app/schema_mariadb.sql` + `migration_new_tables.sql` +
  `migration_2026_session2..9.sql`: **every table and every column is
  present**; all named indexes and constraints appear in the SQL. (Column
  types were compared loosely; decimals and lengths looked right.)
- Non-native enum columns: the longest member name fits every column length.
- Raw SQL / SQLite-only functions in `app/`: none (the ORM is used
  throughout). `group_by` queries select only the grouped id + aggregates, so
  `ONLY_FULL_GROUP_BY` is not a problem.
- Engine uses `pool_pre_ping=True`, which covers idle-connection drops.
- `pymysql` is in `requirements.txt`.

## Fixed in this change
- **Deadlock risk:** `_reserve_stock` / `_release_stock` locked inventory rows
  in cart order. Two concurrent orders with the same SKUs in opposite order
  deadlock on InnoDB (error 1213 -> HTTP 500); SQLite serialises writers so
  no test could show it. Items are now locked in ascending `sku_id` order.

## Do this before the first deploy
1. **Take a backup, run on a staging database first.** Apply in this order:
   `schema_mariadb.sql`, `migration_new_tables.sql`,
   `migration_2026_session2.sql` ... `session9.sql`
   (session9 = shipments tables + `orders.idempotency_key`). A fresh database can
   alternatively be created straight from the models with
   `python -m app.init_db` (plain `create_all`, dialect-agnostic); use the
   SQL files only for a database that already has an older schema.
2. The migrations use plain `ALTER TABLE ... ADD COLUMN`, so they fail if run
   twice. MariaDB supports `ADD COLUMN IF NOT EXISTS`; add it if you want
   re-runnable scripts.
3. `DATABASE_URL` should name the charset explicitly:
   `mysql+pymysql://USER:PASSWORD@localhost:3306/maruplast?charset=utf8mb4`.
   `.env` currently uses user `maru`; `CLAUDE.md` documents `maruplast`.
   Confirm which one exists on the server.
4. Collation: MariaDB's default `utf8mb4_general_ci` is case-insensitive, so
   unique `email`/`slug` columns treat `A@x.com` and `a@x.com` as duplicates
   (SQLite does not). This is usually what you want, but existing dev data
   should be checked for such pairs.
5. After the first real order, run two checkouts at once for the same SKU and
   confirm one gets 409 `INSUFFICIENT_STOCK` and stock never goes negative
   (this is the path only MariaDB exercises: row locks).
6. Run `pytest` against a scratch MariaDB schema once
   (`tests/conftest.py` forces SQLite today; temporarily point
   `DATABASE_URL`/engine at MariaDB to exercise real locking).
7. Check `SHOW VARIABLES LIKE 'sql_mode'`. Strict mode turns an over-long
   string into an error instead of silently truncating it (SQLite never
   complains), so any field-length mismatch shows up on the first real data.

## Python 3.9 (production server)
The server has Python 3.9; the code used `X | None` (3.10+) in 374
annotations across 56 files. All were rewritten to `Optional[X]` /
`Union[...]` (annotation positions only; the scan found no `|` anywhere
else). Static checks done:
- every file parses with `ast.parse(feature_version=(3, 9))`;
- every file compiles under Python 3.11 (no 3.12+ f-string syntax);
- no `match`, `zip(strict=)`, `datetime.UTC`, `ParamSpec`/`TypeAlias` etc.;
- `pip install --dry-run --python-version 3.9 -r requirements.txt` resolves
  (SQLAlchemy 2.0.54, FastAPI 0.128.8, Pydantic 2.13.5, Starlette 0.49.3).
- the 79-test suite passes (on the dev interpreter).

**Not verified:** actually importing/running on a real 3.9. On the server,
before anything else: create a venv, `pip install -r requirements.txt`,
`python -c "import app.main"`, run `pytest -q`. Requirements are unpinned;
after a green run, `pip freeze > requirements.lock` so production matches.
