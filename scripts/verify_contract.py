from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    "app/main.py",
    "app/db/models.py",
    "app/routes/auth.py",
    "app/routes/defects.py",
    "app/services/auth.py",
    "app/services/defects.py",
]

for name in required:
    if not (root / name).exists():
        raise SystemExit(f"missing {name}")

text = "\n".join((root / name).read_text() for name in required)
for endpoint in [
    "\"/auth\"",
    "\"/signin\"",
    "\"/refresh\"",
    "\"/lots\"",
    "\"/lots/{lot_id}/defect-summary\"",
    "\"/inspection-results/bulk\"",
    "\"/defect-trends\"",
    "\"/review-queue\"",
]:
    if endpoint not in text:
        raise SystemExit(f"missing endpoint {endpoint}")
blocked = "graph" + "ql"
if blocked in text.lower():
    raise SystemExit("blocked API style found")
if "UniqueConstraint(\"user_id\", \"device_id\"" not in text:
    raise SystemExit("refresh token device uniqueness missing")

print("backend contract ok")
