from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, page_params, paged
from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobOut, JobStatsOut
from app.services import jobs
from app.services.audit import log_audit

router = APIRouter(prefix="/admin/jobs", tags=["admin-jobs"])


@router.get("/", response_model=list[JobOut])
def list_jobs(
    response: Response,
    status_filter: Optional[str] = None,
    params: PageParams = Depends(page_params),
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
) -> list[Job]:
    stmt = select(Job).order_by(Job.id.desc())
    if status_filter:
        stmt = stmt.where(Job.status == status_filter)
    return paged(db, response, stmt, stmt, params)


@router.get("/stats", response_model=JobStatsOut)
def job_stats(user: User = Depends(require_role(UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)) -> dict:
    return jobs.queue_stats(db)


@router.post("/{job_id}/retry", response_model=JobOut)
def retry_job(job_id: int, user: User = Depends(require_role(UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)) -> Job:
    job = jobs.retry_dead(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Only a dead job can be retried")
    log_audit(db, user, "job_retried", "job", job.id, new={"job_type": job.job_type})
    db.commit()
    return job
