import enum


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    SUPER_ADMIN = "super_admin"
    PRODUCT_MANAGER = "product_manager"
    SALES_MANAGER = "sales_manager"
    WAREHOUSE_MANAGER = "warehouse_manager"
    ACCOUNTANT = "accountant"
    MARKETING_MANAGER = "marketing_manager"


class CustomerType(str, enum.Enum):
    RETAIL = "retail"
    WHOLESALE = "wholesale"
    DISTRIBUTOR = "distributor"
    EXPORT = "export"
    SPECIAL = "special"


class OrderStatus(str, enum.Enum):
    NEW = "new"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    PROCESSING = "processing"
    PACKED = "packed"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"
    # PRD ТЗ№2 §60 alternate state: a payment attempt failed (declined,
    # expired, or explicitly cancelled by the provider before completion).
    # Distinct from CANCELLED, which is customer/admin-initiated.
    PAYMENT_FAILED = "payment_failed"
    # Not in PRD §60's order-status list (PRD §23 has it only as a *payment*
    # status), but the order needs a header-level state for "some, not all,
    # money has been refunded" so admins can see it without summing refunds.
    PARTIALLY_REFUNDED = "partially_refunded"


class ShipmentStatus(str, enum.Enum):
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class PaymentStatus(str, enum.Enum):
    """PRD ТЗ№4 §23. Kept on each payments row and mirrored on orders.payment_status."""

    CREATED = "created"
    PENDING = "pending"
    AUTHORIZED = "authorized"  # reserved for card holds; no gateway here authorizes without capturing yet
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
