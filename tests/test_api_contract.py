from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_api_exposes_health_and_defect_routes() -> None:
    main = (ROOT / "app/main.py").read_text()
    defects = (ROOT / "app/routes/defects.py").read_text()

    assert '@app.get("/health")' in main
    assert "app.include_router(defects_router" in main
    assert "defect-summary" in defects
    assert "review-queue" in defects
