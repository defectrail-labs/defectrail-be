from collections import defaultdict
from datetime import datetime

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import InspectionResult, Lot, Machine, Product, ReviewDecision, ReviewQueue
from app.schemas import BulkInspectionIn


async def list_lots(session: AsyncSession) -> dict:
    rows = (await session.execute(_lot_query())).all()
    lots = [_lot_out(row) for row in rows]
    machine_scores = _machine_scores(rows)
    top_defects = await _top_defects(session)
    return {"lots": lots, "machineScores": machine_scores, "topDefects": top_defects}


async def lot_summary(session: AsyncSession, lot_id: str) -> dict:
    row = (await session.execute(_lot_query().where(Lot.id == lot_id))).first()
    if not row:
        raise ValueError("lot not found")
    defects = await _top_defects(session, lot_id)
    trend_rows = (
        await session.execute(
            select(
                func.strftime("%H:00", InspectionResult.time).label("bucket"),
                func.avg(InspectionResult.score).label("score"),
                func.avg(case((InspectionResult.ai_label == "defect", 1), else_=0)).label("defect_rate"),
            )
            .where(InspectionResult.lot_id == lot_id)
            .group_by("bucket")
            .order_by("bucket")
        )
    ).all()
    images = (
        await session.execute(
            select(InspectionResult)
            .where(InspectionResult.lot_id == lot_id)
            .order_by(InspectionResult.time.desc())
            .limit(20)
        )
    ).scalars()
    return {
        "lot": _lot_out(row),
        "defectTypes": defects,
        "trend": [
            {"bucket": bucket, "defectRate": round((defect_rate or 0) * 100, 1), "score": round(score or 0, 2)}
            for bucket, score, defect_rate in trend_rows
        ],
        "images": [
            {
                "imageId": image.image_id,
                "defectType": image.defect_type,
                "score": image.score,
                "aiLabel": image.ai_label,
            }
            for image in images
        ],
    }


async def bulk_insert(session: AsyncSession, payload: BulkInspectionIn) -> dict[str, int]:
    session.add_all([InspectionResult(**item.model_dump()) for item in payload.results])
    await session.commit()
    return {"inserted": len(payload.results)}


async def trends(session: AsyncSession, group_by: str) -> list[dict]:
    column = {
        "hour": func.strftime("%H:00", InspectionResult.time),
        "machine": Machine.name,
        "lot": Lot.lot_no,
    }.get(group_by, func.strftime("%H:00", InspectionResult.time))
    query = select(
        column.label("group"),
        func.count(InspectionResult.id).label("sample_count"),
        func.avg(case((InspectionResult.ai_label == "defect", 1), else_=0)).label("defect_rate"),
    ).join(Lot, Lot.id == InspectionResult.lot_id)
    if group_by == "machine":
        query = query.join(Machine, Machine.id == InspectionResult.machine_id)
    rows = (await session.execute(query.group_by("group").order_by("group"))).all()
    return [
        {"group": group, "sampleCount": sample_count, "defectRate": round((defect_rate or 0) * 100, 1)}
        for group, sample_count, defect_rate in rows
    ]


async def review_queue(session: AsyncSession) -> list[dict]:
    rows = (
        await session.execute(
            select(ReviewQueue, Lot)
            .join(Lot, Lot.id == ReviewQueue.lot_id)
            .order_by(ReviewQueue.created_at.desc())
        )
    ).all()
    return [
        {
            "id": item.id,
            "lotId": lot.id,
            "lotNo": lot.lot_no,
            "reason": item.reason,
            "status": item.status,
            "assignedTo": item.assigned_to,
            "createdAt": item.created_at,
        }
        for item, lot in rows
    ]


async def update_review(session: AsyncSession, queue_id: str, status: str, memo: str) -> dict:
    item = await session.get(ReviewQueue, queue_id)
    if not item:
        raise ValueError("review queue item not found")
    item.status = status
    session.add(ReviewDecision(queue_id=queue_id, decision=status, memo=memo))
    await session.commit()
    return {"id": queue_id, "status": status}


def _lot_query() -> Select:
    return (
        select(
            Lot,
            Product,
            Machine.name.label("machine_name"),
            func.count(InspectionResult.id).label("sample_count"),
            func.avg(case((InspectionResult.ai_label == "defect", 1), else_=0)).label("defect_rate"),
        )
        .join(Product, Product.id == Lot.product_id)
        .join(InspectionResult, InspectionResult.lot_id == Lot.id)
        .join(Machine, Machine.id == InspectionResult.machine_id)
        .group_by(Lot.id, Product.id, Machine.name)
        .order_by(func.avg(case((InspectionResult.ai_label == "defect", 1), else_=0)).desc())
    )


def _lot_out(row: tuple) -> dict:
    lot, product, machine_name, sample_count, defect_rate = row
    rate = round((defect_rate or 0) * 100, 1)
    return {
        "id": lot.id,
        "lotNo": lot.lot_no,
        "productSku": product.sku,
        "productName": product.name,
        "machine": machine_name,
        "startedAt": lot.started_at,
        "defectRate": rate,
        "sampleCount": sample_count,
        "status": "shipping_hold" if rate >= 5 else "review" if rate >= 2 else "released",
    }


def _machine_scores(rows: list[tuple]) -> list[dict]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        buckets[row.machine_name].append(row.defect_rate or 0)
    return [
        {"machine": machine, "score": round(1 - (sum(rates) / len(rates)), 2), "defectRate": round(sum(rates) / len(rates) * 100, 1)}
        for machine, rates in buckets.items()
    ]


async def _top_defects(session: AsyncSession, lot_id: str | None = None) -> list[dict]:
    query = select(InspectionResult.defect_type, func.count().label("count")).where(InspectionResult.ai_label == "defect")
    if lot_id:
        query = query.where(InspectionResult.lot_id == lot_id)
    rows = (await session.execute(query.group_by(InspectionResult.defect_type).order_by(func.count().desc()))).all()
    total = sum(count for _, count in rows) or 1
    return [{"type": defect_type, "count": count, "rate": round(count / total * 100, 1)} for defect_type, count in rows]
