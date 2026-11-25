"""Read-only verification of API paths used by the React dashboard."""
from app.main import app

required = {
    ("post", "/api/v1/auth/login"),
    ("get", "/api/v1/auth/me"),
    ("get", "/api/v1/news/"),
    ("get", "/api/v1/news/{article_id}"),
    ("get", "/api/v1/knowledge/stats"),
    ("get", "/api/v1/projects/stats"),
    ("get", "/api/v1/skills/stats"),
    ("get", "/api/v1/projects/"),
    ("get", "/api/v1/projects/{project_id}/tasks"),
    ("get", "/api/v1/skills/"),
    ("get", "/api/v1/progress/goals"),
    ("post", "/api/v1/briefing/generate"),
    ("post", "/api/v1/chat/ask"),
    ("get", "/api/v1/briefings/latest"),
}
spec = app.openapi()
found = {
    (method, path)
    for path, methods in spec.get("paths", {}).items()
    for method in methods
    if method in {"get", "post", "put", "patch", "delete"}
}
missing = sorted(required - found)
for method, path in sorted(required):
    print(("PASS" if (method, path) in found else "MISSING") + ": " + method.upper() + " " + path)
if missing:
    raise SystemExit("Frontend API contract has missing routes")
print("\nPASS: All dashboard routes found. No database changes made.")
