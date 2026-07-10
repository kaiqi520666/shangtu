from dataclasses import dataclass

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class PaginationParams:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def pagination_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


async def execute_pagination(
    db: AsyncSession,
    *,
    count_statement,
    data_statement,
    pagination: PaginationParams,
):
    total = int((await db.execute(count_statement)).scalar_one() or 0)
    result = await db.execute(
        data_statement.offset(pagination.offset).limit(pagination.page_size)
    )
    return total, result


def page_payload(items: list[dict], total: int, page: int, page_size: int) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
