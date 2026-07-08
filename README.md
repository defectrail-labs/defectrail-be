# DefectRail BE

FastAPI + SQLAlchemy 2.0 Async Mode REST API for Inspection AI lot quality evidence.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
python scripts/verify_contract.py
```

Default DB is `sqlite+aiosqlite:///./defectrail.db` for cheap local demos. Set `DATABASE_URL` to async Postgres for production-style runs.

Demo user:

```text
email: operator@defectrail.local
password: defectrail
device_id: portfolio-device
```

## API List

- `POST /api/v1/auth/signin`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/lots`
- `GET /api/v1/lots/{lot_id}/defect-summary`
- `POST /api/v1/inspection-results/bulk`
- `GET /api/v1/defect-trends?groupBy=hour|machine|lot`
- `GET /api/v1/review-queue`
- `PATCH /api/v1/review-queue/{queue_id}`

## Demo Backend Adaptation

- Nest service/repository/auth flow -> Python service functions and REST routers.
- Drizzle schema -> SQLAlchemy async declarative models.
- Refresh token hardening preserved: hashed refresh tokens and unique `(user_id, device_id)`.
- Auth identity uniqueness preserved: unique `(provider, provider_user_id)`.
- GraphQL removed.

## DB Optimization Lab

Target bottleneck:

```sql
SELECT lot_id, defect_type, count(*)
FROM inspection_results
WHERE lot_id = :lot_id
  AND time BETWEEN :from AND :to
GROUP BY lot_id, defect_type;
```

Index evidence:

```text
before: sequential scan on inspection_results, 100k-row demo, p95 target breach
after: ix_inspection_lot_time_defect(lot_id, time, defect_type), expected index range scan
```

TimescaleDB upgrade path:

```sql
SELECT create_hypertable('inspection_results', 'time');
CREATE MATERIALIZED VIEW lot_defect_summary AS ...
```

## Portfolio Evidence

- Async SQLAlchemy models for RDB entities and time-series inspection results.
- REST ingest, dashboard summary, trend, review queue, and token endpoints.
- Mock seed data for lots, inspection results, defect rules, and review decisions.
- Verification script proving required routes and no GraphQL.

## Resume Bullets

- Implemented a FastAPI + SQLAlchemy 2.0 Async Mode REST API for lot-level Inspection AI defect analytics.
- Adapted demo-backend auth/token concepts into hashed refresh tokens with per-device uniqueness.
- Modeled lots, machines, inspection results, defect trends, and review queues for RDB/TSDB optimization evidence.
