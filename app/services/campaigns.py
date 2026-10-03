"""Newsletter campaigns and one-off e-mails sent by admins.

A campaign goes to CONFIRMED subscribers only (double opt-in), each mail carries that person's own unsubscribe link,
and each recipient is a job (`newsletter.send`): retried on SMTP trouble, one failure never stops the rest. Gmail and
most shared SMTP accounts cap sending (Gmail: about 500 messages a day) - use a transactional mail service for big lists.
"""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models.newsletter_campaign import NewsletterCampaign
from app.models.newsletter_subscriber import NewsletterStatus, NewsletterSubscriber
from app.services.jobs import PermanentJobError, enqueue, job_handler, run_pending
from app.services.notifications.email import EmailNotifier

INLINE_LIMIT = 25  # without a worker, small sends still go out immediately; bigger ones wait for the worker


def footer(token: str) -> str:
    link = f"{settings.FRONTEND_URL.rstrip('/')}/newsletter/unsubscribe?token={token}"
    return f"\n\n--\nMARU\nTo stop receiving these e-mails: {link}"


def recipients(db: Session, locale: str = None) -> list:
    stmt = select(NewsletterSubscriber).where(NewsletterSubscriber.status == NewsletterStatus.CONFIRMED)
    if locale:
        stmt = stmt.where(NewsletterSubscriber.locale == locale)
    return list(db.execute(stmt.order_by(NewsletterSubscriber.id)).scalars())


def start_campaign(db: Session, subject: str, body: str, locale, admin_id: int) -> NewsletterCampaign:
    subs = recipients(db, locale)
    campaign = NewsletterCampaign(subject=subject.strip(), body=body, locale=locale, recipients_total=len(subs), created_by_user_id=admin_id)
    db.add(campaign)
    db.flush()
    for sub in subs:
        enqueue(db, "newsletter.send", {"campaign_id": campaign.id, "subscriber_id": sub.id}, dedupe_key=f"camp:{campaign.id}:{sub.id}", commit=False)
    db.commit()
    if not settings.JOBS_ASYNC and len(subs) <= INLINE_LIMIT:
        run_pending(db, "inline", limit=len(subs))
        db.refresh(campaign)
    return campaign


@job_handler("newsletter.send")
def _send_job(db: Session, payload: dict) -> None:
    campaign = db.get(NewsletterCampaign, payload["campaign_id"])
    sub = db.get(NewsletterSubscriber, payload["subscriber_id"])
    if campaign is None or sub is None or sub.status != NewsletterStatus.CONFIRMED:
        # Unsubscribed (or removed) between queueing and sending: never mail them.
        if campaign is not None:
            db.execute(update(NewsletterCampaign).where(NewsletterCampaign.id == campaign.id).values(recipients_total=NewsletterCampaign.recipients_total - 1))
            db.commit()
        raise PermanentJobError("The subscriber is no longer on the list")
    EmailNotifier(raise_errors=True).custom(sub.email, campaign.subject, campaign.body + footer(sub.token))
    db.execute(update(NewsletterCampaign).where(NewsletterCampaign.id == campaign.id).values(sent_count=NewsletterCampaign.sent_count + 1))
    db.commit()


def progress(db: Session, campaign: NewsletterCampaign) -> dict:
    """Live numbers: sent from the counter, failed = jobs that ended dead, waiting = still pending/running."""
    from app.models.job import JOB_DEAD, JOB_PENDING, JOB_RUNNING, Job

    prefix = f"camp:{campaign.id}:%"
    rows = dict(db.execute(select(Job.status, func.count()).where(Job.dedupe_key.like(prefix)).group_by(Job.status)).all())
    return {"sent": campaign.sent_count, "failed": rows.get(JOB_DEAD, 0), "waiting": rows.get(JOB_PENDING, 0) + rows.get(JOB_RUNNING, 0)}
