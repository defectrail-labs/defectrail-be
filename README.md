# DefectRail BE

Inspection AI lot 품질 데이터를 제공하는 FastAPI + SQLAlchemy 2.0 Async Mode REST API입니다.

## 주요 기능

- 로그인/refresh token 인증
- lot 목록과 상세 defect summary
- 검사 결과 bulk ingest
- defect trend 집계
- review queue 상태 변경
- SQLAlchemy async 모델 기반 RDB/TSDB 확장 구조

## 기술 스택

- FastAPI
- SQLAlchemy 2.0 Async Mode
- aiosqlite local demo
- PostgreSQL/TimescaleDB 확장 가능 설계

## 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## 검증

```bash
python scripts/verify_contract.py
python -m compileall app
```

## API

- `POST /api/v1/auth/signin`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/lots`
- `GET /api/v1/lots/{lot_id}/defect-summary`
- `POST /api/v1/inspection-results/bulk`
- `GET /api/v1/defect-trends`
- `GET /api/v1/review-queue`
- `PATCH /api/v1/review-queue/{queue_id}`

## 프로젝트 포인트

비동기 ORM, token hardening, lot 단위 집계 API, review queue를 한 흐름으로 묶었습니다. REST API만 사용합니다.
