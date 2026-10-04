"""Packing parameters of an order or cart (PRD ТЗ№1 §18): how many boxes, how heavy, how much space.

For each line: if the SKU has a box size (`box_quantity`), full and partial boxes are counted (50 x 350 ml in
boxes of 24 = 3 boxes, the last one partly filled) and the weight is the units plus the empty boxes. Without a
box size the units are shipped loose: weight is the unit weight, volume the unit's own dimensions (if known).
Missing data is reported through `complete`, so the caller can say "approximate".
"""

from dataclasses import dataclass, field
from math import ceil
from typing import Iterable, Optional


@dataclass
class Packaging:
    boxes: int = 0
    loose_units: int = 0
    weight_g: int = 0
    volume_cm3: float = 0.0
    complete: bool = True  # False when some line lacked weight or size data
    lines: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "boxes": self.boxes,
            "loose_units": self.loose_units,
            "weight_kg": round(self.weight_g / 1000, 2),
            "volume_l": round(self.volume_cm3 / 1000, 2),
            "complete": self.complete,
        }


def _mm3_to_cm3(a: Optional[int], b: Optional[int], c: Optional[int]) -> Optional[float]:
    if not (a and b and c):
        return None
    return a * b * c / 1000.0


def packaging_for(lines: Iterable) -> Packaging:
    """`lines` is an iterable of (sku, quantity)."""
    out = Packaging()
    for sku, qty in lines:
        row = {"sku": sku.sku_code, "quantity": qty, "boxes": 0, "loose": 0}
        unit_g = sku.unit_weight_g
        if sku.box_quantity and sku.box_quantity > 0:
            boxes = ceil(qty / sku.box_quantity)
            row["boxes"] = boxes
            out.boxes += boxes
            if unit_g is None:
                out.complete = False
            out.weight_g += (unit_g or 0) * qty + (sku.box_weight_g or 0) * boxes
            if sku.box_weight_g is None:
                out.complete = False
            volume = _mm3_to_cm3(sku.box_length_mm, sku.box_width_mm, sku.box_height_mm)
            if volume is None:
                out.complete = False
            else:
                out.volume_cm3 += volume * boxes
        else:
            row["loose"] = qty
            out.loose_units += qty
            if unit_g is None:
                out.complete = False
            out.weight_g += (unit_g or 0) * qty
            product = sku.variant.product if getattr(sku, "variant", None) is not None else None
            volume = _mm3_to_cm3(getattr(product, "length_mm", None), getattr(product, "width_mm", None), getattr(product, "height_mm", None))
            if volume is None:
                out.complete = False
            else:
                out.volume_cm3 += volume * qty
        out.lines.append(row)
    return out
