"""Remove the placeholder data added while the shop had no real catalogue (see IMAGE_CREDITS.md).

What it removes
  * the demo products (slug starts with "demo-") with their variants, SKUs, stock and photos;
  * the "gbgf" test product (slug "vcb");
  * with --original-photos: the Wikimedia Commons photos that were put first on the three original products.
Orders are never touched. A product whose SKUs appear on an order is skipped and reported.

Usage (from the project root, with the same DATABASE_URL the backend uses):
    python scripts/remove_demo_data.py            # dry run: prints what would be deleted, changes nothing
    python scripts/remove_demo_data.py --apply    # really deletes (take a database backup first)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select  # noqa: E402

from app.database import Base, SessionLocal  # noqa: E402
import app.models  # noqa: E402,F401  (registers every table)

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "app" / "static" / "uploads"


def children(table_name):
    """(child table, fk column) pairs that point at <table_name>'s primary key."""
    target = Base.metadata.tables[table_name]
    pk_cols = set(target.primary_key.columns)
    found = []
    for child in Base.metadata.sorted_tables:
        for fk in child.foreign_keys:
            if fk.column.table is target and fk.column in pk_cols:
                found.append((child, fk.parent))
    return found


def cascade_delete(db, table_name, ids, counts):
    """Delete rows of <table_name> with these primary keys, children first."""
    if not ids:
        return
    table = Base.metadata.tables[table_name]
    (pk,) = list(table.primary_key.columns)
    for child, fk_col in children(table_name):
        if child.name == table_name:
            continue
        if child.name == "order_items":
            continue  # sold products are skipped before we get here (see main)
        child_pks = list(child.primary_key.columns)
        if len(child_pks) == 1:
            child_ids = [r[0] for r in db.execute(select(child_pks[0]).where(fk_col.in_(ids)))]
            cascade_delete(db, child.name, child_ids, counts)
        else:
            res = db.execute(delete(child).where(fk_col.in_(ids)))
            counts[child.name] = counts.get(child.name, 0) + (res.rowcount or 0)
    res = db.execute(delete(table).where(pk.in_(ids)))
    counts[table_name] = counts.get(table_name, 0) + (res.rowcount or 0)


def image_files(url):
    """The original upload and its generated copies for an image URL."""
    name = url.rsplit("/", 1)[-1]
    stem = name.rsplit(".", 1)[0]
    return [p for p in UPLOAD_DIR.glob(stem + "*") if p.is_file()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="really delete (default is a dry run)")
    ap.add_argument("--original-photos", action="store_true", help="also remove the Commons photos on the 3 original products")
    args = ap.parse_args()

    from app.models.product import Product
    from app.models.order_item import OrderItem
    from app.models.product_variant import ProductVariant
    from app.models.sku import SKU
    from app.models.variant_image import VariantImage

    db = SessionLocal()
    counts = {}
    files = []
    skipped = []
    try:
        products = db.execute(
            select(Product).where((Product.slug.like("demo-%")) | (Product.slug == "vcb"))
        ).scalars().all()
        for product in products:
            variant_ids = [v.id for v in db.execute(select(ProductVariant).where(ProductVariant.product_id == product.id)).scalars()]
            urls = [u for (u,) in db.execute(select(VariantImage.image_url).where(VariantImage.variant_id.in_(variant_ids)))] if variant_ids else []
            sku_ids = [r[0] for r in db.execute(select(SKU.id).where(SKU.variant_id.in_(variant_ids)))] if variant_ids else []
            if sku_ids and db.execute(select(OrderItem.id).where(OrderItem.sku_id.in_(sku_ids)).limit(1)).first():
                skipped.append((product.name, "appears on an order"))
                continue
            cascade_delete(db, "products", [product.id], counts)
            for u in urls:
                files.extend(image_files(u))
            print("  product: %s (%s)" % (product.name, product.slug))

        if args.original_photos:
            rows = db.execute(
                select(VariantImage)
                .join(ProductVariant, ProductVariant.id == VariantImage.variant_id)
                .where(ProductVariant.product_id.in_([1, 2, 3]), VariantImage.sort_order < 0)
            ).scalars().all()
            for img in rows:
                files.extend(image_files(img.image_url))
                db.delete(img)
                counts["variant_images (original products)"] = counts.get("variant_images (original products)", 0) + 1
            db.flush()

        print("\nRows %s:" % ("deleted" if args.apply else "that would be deleted"))
        for name, n in sorted(counts.items()):
            print("  %-40s %d" % (name, n))
        uniq = sorted(set(files))
        print("Photo files %s: %d" % ("deleted" if args.apply else "that would be deleted", len(uniq)))
        for name, why in skipped:
            print("SKIPPED %s: %s" % (name, why))

        if args.apply:
            db.commit()
            for f in uniq:
                f.unlink(missing_ok=True)
            print("\nDone.")
        else:
            db.rollback()
            print("\nDry run only, nothing changed. Run again with --apply to delete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
