#!/usr/bin/env python3
"""
Verify script for Hotel Automation Engine.
Checks app structure, imports, and basic functionality.
"""
import sys
import os
import importlib
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        print(f"  {GREEN}✓{RESET} {name}")
        passed += 1
    else:
        print(f"  {RED}✗{RESET} {name} — {detail}")
        failed += 1


def section(title: str):
    print(f"\n{'─'*50}")
    print(f" {title}")
    print(f"{'─'*50}")


# ── 1. File Structure ─────────────────────────────────────────────────────
section("1. File Structure")

required_paths = [
    "app/__init__.py", "app/main.py", "app/config.py", "app/database.py",
    "app/models.py", "app/schemas.py",
    "app/agents/__init__.py", "app/agents/base.py",
    "app/agents/orchestrator.py", "app/agents/guest_agent.py",
    "app/agents/ops_agent.py", "app/agents/hsk_agent.py",
    "app/agents/revenue_agent.py",
    "app/routes/__init__.py", "app/routes/agents.py",
    "app/routes/operations.py", "app/routes/analytics.py",
    "app/routes/webhooks.py",
    "app/adapters/__init__.py", "app/adapters/schema_org.py",
    "app/services/__init__.py", "app/services/pricing_engine.py",
    "scripts/seed_demo.py",
    "tests/test_engine.py",
    "Dockerfile", "docker-compose.yml",
    "requirements.txt", "pyproject.toml", ".env.example",
]

for p in required_paths:
    check(f"{p} exists", (ROOT / p).exists(), f"Missing: {p}")

# ── 2. Python Imports ─────────────────────────────────────────────────────
section("2. Python Imports")

modules = [
    "app.config", "app.database", "app.models", "app.schemas",
    "app.agents.base", "app.agents.orchestrator",
    "app.agents.guest_agent", "app.agents.ops_agent",
    "app.agents.hsk_agent", "app.agents.revenue_agent",
    "app.adapters.schema_org", "app.services.pricing_engine",
    "app.routes.agents", "app.routes.operations",
    "app.routes.analytics", "app.routes.webhooks",
]

for mod_name in modules:
    try:
        importlib.import_module(mod_name)
        check(f"import {mod_name}", True)
    except Exception as e:
        check(f"import {mod_name}", False, str(e)[:80])

# ── 3. App Creation ───────────────────────────────────────────────────────
section("3. Application Startup")

try:
    from app.main import app
    check("FastAPI app created", True)
    # Check routes
    routes = [r.path for r in app.routes]
    expected_routes = [
        "/health", "/",
        "/.well-known/ai-agent.json",
        "/api/v1/agents/execute",
        "/api/v1/agents/status",
        "/api/v1/agents/recent",
        "/api/v1/agent-inventory/hotel",
        "/api/v1/agent-inventory/rooms",
        "/api/v1/agent-inventory/availability",
        "/api/v1/analytics/metrics",
        "/api/v1/operations/maintenance",
        "/api/v1/operations/housekeeping",
        "/api/v1/webhooks/pms/booking-created",
    ]
    for route in expected_routes:
        if route in routes:
            check(f"route '{route}' registered", True)
        else:
            check(f"route '{route}' registered", False, f"Expected {route} in routes")
except Exception as e:
    check("FastAPI app creation", False, str(e)[:120])

# ── 4. Content Analysis ───────────────────────────────────────────────────
section("4. Code Statistics")

total_lines = 0
total_files = 0
py_files = list(ROOT.rglob("*.py")) + list(ROOT.rglob("*.yml")) + list(ROOT.rglob("*.toml"))
py_files = [f for f in py_files if ".venv" not in str(f)]

for f in py_files:
    try:
        lines = len(f.read_text().splitlines())
        total_lines += lines
        total_files += 1
    except Exception:
        pass

print(f"  Files: {total_files}")
print(f"  Lines of code: {total_lines}")
check("Codebase has substance", total_lines > 500, f"Only {total_lines} lines")

# ── Summary ───────────────────────────────────────────────────────────────
section("Summary")
print(f"\n  {GREEN}{passed} passed{RESET} · {RED if failed else ''}{failed} failed{RESET} of {passed + failed}")

if failed == 0:
    print(f"\n  {GREEN}✅ All checks passed!{RESET}")
else:
    print(f"\n  {RED}❌ {failed} check(s) failed{RESET}")

sys.exit(1 if failed > 0 else 0)
