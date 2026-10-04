"""PRD ТЗ№1 §18: boxes, weight and volume of an order."""

from types import SimpleNamespace

from app.services.packaging import packaging_for


def _sku(code="S", unit_g=20, box_qty=24, box_g=300, box_dims=(300, 200, 150), product_dims=(100, 100, 50)):
    product = SimpleNamespace(length_mm=product_dims[0], width_mm=product_dims[1], height_mm=product_dims[2])
    return SimpleNamespace(
        sku_code=code, unit_weight_g=unit_g, box_quantity=box_qty, box_weight_g=box_g,
        box_length_mm=box_dims[0], box_width_mm=box_dims[1], box_height_mm=box_dims[2],
        variant=SimpleNamespace(product=product),
    )


def test_fifty_units_in_boxes_of_24_is_three_boxes():
    p = packaging_for([(_sku(), 50)])
    assert p.boxes == 3 and p.loose_units == 0
    assert p.weight_g == 50 * 20 + 3 * 300            # units + empty boxes
    assert p.volume_cm3 == 3 * (300 * 200 * 150 / 1000)
    assert p.complete and p.as_dict() == {"boxes": 3, "loose_units": 0, "weight_kg": 1.9, "volume_l": 27.0, "complete": True}


def test_loose_units_use_their_own_size_and_mixed_lines_add_up():
    loose = _sku("L", unit_g=15, box_qty=None, box_g=None)
    p = packaging_for([(_sku(), 24), (loose, 10)])
    assert p.boxes == 1 and p.loose_units == 10
    assert p.weight_g == (24 * 20 + 300) + 10 * 15
    assert p.volume_cm3 == 300 * 200 * 150 / 1000 + 10 * (100 * 100 * 50 / 1000)


def test_missing_data_is_flagged_not_guessed():
    p = packaging_for([(_sku(unit_g=None, box_g=None, box_dims=(None, None, None)), 5)])
    assert p.boxes == 1 and p.weight_g == 0 and p.complete is False
    assert packaging_for([]).as_dict()["boxes"] == 0


def test_cart_api_reports_packaging(client, db_session, sku):
    sku.unit_weight_g, sku.box_quantity, sku.box_weight_g = 20, 4, 100
    sku.box_length_mm, sku.box_width_mm, sku.box_height_mm = 200, 100, 100
    db_session.commit()
    r = client.get("/api/v1/cart/")
    tok = r.headers.get("x-cart-token") or r.json().get("token")
    client.post("/api/v1/cart/items", json={"sku_id": sku.id, "quantity": 9}, headers={"X-Cart-Token": tok})
    pack = client.get("/api/v1/cart/", headers={"X-Cart-Token": tok}).json()["packaging"]
    assert pack["boxes"] == 3 and pack["weight_kg"] == 0.48 and pack["volume_l"] == 6.0 and pack["complete"] is True
