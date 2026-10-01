"""Shared paging for list endpoints (PRD ТЗ№3 §51): `?page=` and `?limit=` with a hard
maximum page size, and the number of matches in the X-Total-Count header so clients can
page through everything."""

from dataclasses import dataclass

from fastapi import Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 50


@dataclass
class PageParams:
    page: int
    limit: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def page_params(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> PageParams:
    return PageParams(page=page, limit=limit)


def paged(db: Session, response: Response, stmt, count_stmt, params: PageParams, unique: bool = False) -> list:
    """Runs `stmt` for one page. `count_stmt` is the same query WITHOUT eager-load options
    (it is only used to count the matches, ignoring paging)."""
    total = db.execute(select(func.count()).select_from(count_stmt.order_by(None).subquery())).scalar_one()
    response.headers["X-Total-Count"] = str(total)
    result = db.execute(stmt.offset(params.offset).limit(params.limit))
    return list(result.unique().scalars().all() if unique else result.scalars().all())


def paged_rows(db: Session, response: Response, stmt, count_stmt, params: PageParams) -> list:
    """Like paged(), for a statement that selects several columns / entities: returns the rows themselves."""
    total = db.execute(select(func.count()).select_from(count_stmt.order_by(None).subquery())).scalar_one()
    response.headers["X-Total-Count"] = str(total)
    return list(db.execute(stmt.offset(params.offset).limit(params.limit)).all())
