from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas import BulkInspectionIn, DashboardOut, ReviewPatch, ReviewQueueOut
from app.services import defects

router = APIRouter(tags=["defects"])


@router.get("/lots", response_model=DashboardOut)
async def lots_route(session: AsyncSession = Depends(get_session)) -> dict:
    return await defects.list_lots(session)


@router.get("/lots/{lot_id}/defect-summary")
async def lot_summary_route(lot_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    try:
        return await defects.lot_summary(session, lot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/inspection-results/bulk")
async def bulk_inspection_route(payload: BulkInspectionIn, session: AsyncSession = Depends(get_session)) -> dict[str, int]:
    return await defects.bulk_insert(session, payload)


@router.get("/defect-trends")
async def defect_trends_route(
    groupBy: str = Query(default="hour", pattern="^(hour|machine|lot)$"),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await defects.trends(session, groupBy)


@router.get("/review-queue", response_model=list[ReviewQueueOut])
async def review_queue_route(session: AsyncSession = Depends(get_session)) -> list[dict]:
    return await defects.review_queue(session)


@router.patch("/review-queue/{queue_id}")
async def review_patch_route(
    queue_id: str,
    payload: ReviewPatch,
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        return await defects.update_review(session, queue_id, payload.status, payload.memo)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
