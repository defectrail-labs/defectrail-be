from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DefectRule, InspectionResult, Lot, Machine, Product, ReviewQueue
from app.services.auth import ensure_demo_user


async def seed_mock_data(session: AsyncSession) -> None:
    if await session.scalar(select(Product).limit(1)):
        return

    await ensure_demo_user(session)
    product_a = Product(id="prod-cell-8k", sku="CELL-8K", name="Battery Cell 8K", spec_version="v3.2")
    product_b = Product(id="prod-cam-lens", sku="CAM-LENS", name="Camera Lens", spec_version="v1.8")
    machines = [
        Machine(id="machine-aoi-01", name="AOI-01", line_code="L1"),
        Machine(id="machine-aoi-02", name="AOI-02", line_code="L1"),
        Machine(id="machine-aoi-03", name="AOI-03", line_code="L2"),
    ]
    base = datetime(2026, 7, 8, 8, 0, 0)
    lots = [
        Lot(id="lot-2407-a", product_id=product_a.id, lot_no="DR-2407-A", started_at=base),
        Lot(id="lot-2407-b", product_id=product_a.id, lot_no="DR-2407-B", started_at=base + timedelta(hours=1)),
        Lot(id="lot-2407-c", product_id=product_b.id, lot_no="DR-2407-C", started_at=base + timedelta(hours=2)),
    ]
    session.add_all([product_a, product_b, *machines, *lots])
    session.add_all(
        [
            DefectRule(defect_type="scratch", threshold=0.05, severity="high"),
            DefectRule(defect_type="contamination", threshold=0.03, severity="medium"),
            DefectRule(defect_type="edge_crack", threshold=0.01, severity="critical"),
        ]
    )
    await session.flush()

    rows = []
    defect_plan = {
        "lot-2407-a": ("machine-aoi-03", 68),
        "lot-2407-b": ("machine-aoi-01", 21),
        "lot-2407-c": ("machine-aoi-02", 7),
    }
    for lot_id, (machine_id, defect_count) in defect_plan.items():
        for index in range(100):
            is_defect = index < defect_count
            rows.append(
                InspectionResult(
                    time=base + timedelta(minutes=index),
                    lot_id=lot_id,
                    machine_id=machine_id,
                    image_id=f"{lot_id}-img-{index:04d}",
                    defect_type=["scratch", "contamination", "edge_crack"][index % 3] if is_defect else "none",
                    score=0.92 if is_defect else 0.12,
                    ai_label="defect" if is_defect else "normal",
                )
            )
    session.add_all(rows)
    session.add_all(
        [
            ReviewQueue(
                id="rq-1001",
                lot_id="lot-2407-a",
                reason="scratch rate exceeded rule threshold",
                status="open",
                assigned_to="quality.ops",
            ),
            ReviewQueue(
                id="rq-1002",
                lot_id="lot-2407-b",
                reason="machine score dropped below 0.9",
                status="open",
                assigned_to="line.lead",
            ),
        ]
    )
    await session.commit()
