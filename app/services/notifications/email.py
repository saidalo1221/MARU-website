import logging
import smtplib
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.config import settings
from app.models.order import Order
from app.services.notifications.base import NotificationBase
from app.services.notifications.templates import render_template

logger = logging.getLogger("maru.notifications.email")


class EmailNotifier(NotificationBase):
    """Sends real transactional email over SMTP (PRD section 38). Requires
    SMTP_HOST and SMTP_FROM_EMAIL in .env (SMTP_USER/SMTP_PASSWORD too, unless
    the relay allows anonymous send). Never raises — a notification failure
    must not fail an already-committed order; failures are logged instead."""

    def _send(self, to_email: str, subject: str, body: str) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            logger.warning("Email not sent (SMTP not configured): %s -> %s", subject, to_email)
            return

        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = to_email

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            logger.exception("Failed to send email: %s -> %s", subject, to_email)

    def email_verification(self, to_email: str, token: str, db: Session | None = None) -> None:
        link = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"
        context = {"link": link, "to_email": to_email}
        rendered = render_template(db, "email_verification", context)
        if rendered:
            subject, body = rendered
        else:
            subject = "Verify your MARU account"
            body = (
                f"Confirm your email address (valid for 24 hours):\n{link}\n\n"
                "If you did not create this account, ignore this email.\n\nMARU"
            )
        self._send(to_email, subject, body)

    def password_reset(self, to_email: str, token: str, db: Session | None = None) -> None:
        link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
        context = {"link": link, "to_email": to_email}
        rendered = render_template(db, "password_reset", context)
        if rendered:
            subject, body = rendered
        else:
            subject = "Reset your MARU password"
            body = (
                f"Use this link to set a new password (valid for 1 hour):\n{link}\n\n"
                "If you did not request this, ignore this email.\n\nMARU"
            )
        self._send(to_email, subject, body)

    def admin_login_code(self, to_email: str, code: str, db: Session | None = None) -> None:
        context = {"code": code, "to_email": to_email}
        rendered = render_template(db, "admin_login_code", context)
        if rendered:
            subject, body = rendered
        else:
            subject = "Your MARU admin verification code"
            body = (
                f"Your verification code is: {code}\n\n"
                "It expires in 10 minutes. If you did not request this, ignore this email.\n\nMARU"
            )
        self._send(to_email, subject, body)

    def order_created(self, order: Order, db: Session | None = None) -> None:
        context = {
            "order_number": order.order_number,
            "first_name": order.first_name,
            "total_amount": str(order.total_amount),
            "currency": order.currency,
        }
        rendered = render_template(db, "order_created", context)
        if rendered:
            subject, body = rendered
        else:
            subject = f"Your MARU order {order.order_number} was received"
            body = (
                f"Hi {order.first_name},\n\n"
                f"We received your order {order.order_number} for {order.total_amount} {order.currency}. "
                f"We'll email you as it progresses.\n\nMARU"
            )
        self._send(order.email, subject, body)

    def order_status_changed(self, order: Order, old_status: str, new_status: str, db: Session | None = None) -> None:
        context = {
            "order_number": order.order_number,
            "first_name": order.first_name,
            "old_status": old_status,
            "new_status": new_status,
        }
        rendered = render_template(db, "order_status_changed", context)
        if rendered:
            subject, body = rendered
        else:
            subject = f"Order {order.order_number} is now {new_status}"
            body = (
                f"Hi {order.first_name},\n\n"
                f"Your order {order.order_number} status changed from {old_status} to {new_status}.\n\nMARU"
            )
        self._send(order.email, subject, body)
