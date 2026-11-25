"""AI-Pulse project completion audit."""

from pathlib import Path
from collections import Counter
import re

from fastapi.routing import APIRoute
from app.main import app

root = Path("app")

print("\n========== AI-PULSE PROJECT AUDIT ==========\n")

python_files = sorted(root.rglob("*.py"))

print("BACKEND")
print("Python modules:", len(python_files))

routes = [
    route for route in app.routes
    if isinstance(route, APIRoute)
]

print("Registered API endpoints:", len(routes))

groups = Counter()

for route in routes:
    parts = route.path.strip("/").split("/")
    group = (
        parts[3]
        if len(parts) > 3 and parts[:2] == ["api", "v1"]
        else "other"
    )
    groups[group] += 1

print("\nAPI GROUPS")

for group, count in sorted(groups.items()):
    print(f"  {group}: {count}")

print("\nPOSSIBLE INCOMPLETE CODE")

patterns = {
    "TODO/FIXME": re.compile(r"\b(?:TODO|FIXME)\b"),
    "placeholder": re.compile(r"\bplaceholder\b", re.I),
    "NotImplementedError": re.compile(r"\bNotImplementedError\b"),
}

matches = []

for path in python_files:
    contents = path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    for number, line in enumerate(
        contents.splitlines(), start=1
    ):
        found = [
            name
            for name, pattern in patterns.items()
            if pattern.search(line)
        ]

        if found:
            matches.append((
                str(path),
                number,
                ", ".join(found),
            ))

print("Potential incomplete locations:", len(matches))

for filename, line, marker in matches[:60]:
    print(f"  {filename}:{line} [{marker}]")

if len(matches) > 60:
    print("  Additional matches omitted")

print("\nPROJECT COMPONENTS")

components = [
    "frontend",
    "client",
    "web",
    "app/web",
    "tests",
    "alembic",
    "scripts",
    "README.md",
    "requirements.txt",
    "pyproject.toml",
]

for component in components:
    path = Path(component)
    status = "FOUND" if path.exists() else "MISSING"
    print(f"  {component}: {status}")

print("\nTEST INVENTORY")

test_files = list(Path(".").rglob("test_*.py"))

test_files = [
    path for path in test_files
    if not any(
        part in {
            ".venv", "venv", "__pycache__",
            "node_modules", ".git"
        }
        for part in path.parts
    )
]

print("Test files:", len(test_files))

print("\n========== AUDIT COMPLETE ==========")
