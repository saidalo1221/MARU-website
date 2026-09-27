from abc import ABC, abstractmethod

from app.models.order import Order


class CRMBase(ABC):
    """Boundary PRD section 26 requires: every order must automatically be
    pushed to CRM, carrying client/contacts/country/items/quantity/sum/
    currency/delivery/source/payment method/status. No CRM has been chosen
    yet — this lets one be dropped in later without touching the order flow."""

    @abstractmethod
    def push_order(self, order: Order) -> bool:
        """Push this order's current state to the CRM (create or update).
        Returns True on a confirmed successful push, False otherwise (including
        "not configured") — app/services/integrations/log.py uses this to
        decide whether to log a retryable failure."""

    def push_quote(self, quote) -> bool:
        """Push a B2B quote / distributor request to the CRM as a lead.
        No-op (returns False) by default."""
        return False
