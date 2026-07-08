import importlib
import os

from fastapi.testclient import TestClient


def test_defectrail_api_flow(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmp_path / 'defectrail-test.db'}"
    main = importlib.import_module("app.main")

    with TestClient(main.app) as client:
        assert client.get("/health").json()["status"] == "ok"

        signin = client.post(
            "/api/v1/auth/signin",
            json={"email": "operator@defectrail.local", "password": "defectrail", "device_id": "pytest-device"},
        )
        assert signin.status_code == 200
        assert signin.json()["access_token"]

        dashboard = client.get("/api/v1/lots")
        assert dashboard.status_code == 200
        lot = dashboard.json()["lots"][0]
        assert lot["id"].startswith("lot-")

        summary = client.get(f"/api/v1/lots/{lot['id']}/defect-summary")
        assert summary.status_code == 200
        assert summary.json()["lot"]["id"] == lot["id"]

        trends = client.get("/api/v1/defect-trends?groupBy=hour")
        assert trends.status_code == 200
        assert trends.json()[0]["sampleCount"] > 0

        queue = client.get("/api/v1/review-queue")
        assert queue.status_code == 200
        queue_id = queue.json()[0]["id"]

        patched = client.patch(f"/api/v1/review-queue/{queue_id}", json={"status": "approved", "memo": "pytest"})
        assert patched.status_code == 200
        assert patched.json()["status"] == "approved"
