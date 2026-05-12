<div align="center">

# 🏨 Hotel Automation Engine

**Multi-agent AI system for end-to-end hotel operations automation**

![Python](https://img.shields.io/badge/Python-3.11+-0d1117?style=flat-square&logo=python&logoColor=6EE7B7)
![FastAPI](https://img.shields.io/badge/FastAPI-0d1117?style=flat-square&logo=fastapi&logoColor=6EE7B7)
![Docker](https://img.shields.io/badge/Docker-0d1117?style=flat-square&logo=docker&logoColor=6EE7B7)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-0d1117?style=flat-square&logo=python&logoColor=6EE7B7)
![License](https://img.shields.io/badge/License-MIT-0d1117?style=flat-square)

**Production-ready · API-first · 5 specialized AI agents · 12-month demo data**

</div>

---

## 📋 Overview

Hotel Automation Engine is a **production-grade multi-agent system** that orchestrates AI agents across hotel operations — from guest communication and check-in flows to housekeeping scheduling, maintenance ticketing, dynamic pricing, and real-time staff coordination.

Designed for independent hotels and boutique properties that want to reduce manual overhead **without replacing their existing PMS**.

### What It Does

| Agent | Domain | Automates |
|-------|--------|-----------|
| 🎯 **Orchestrator** | Central routing | Routes requests, manages state, coordinates all agents |
| 👤 **Guest Agent** | Guest-facing | Check-in/out, upsells, messaging, late checkout handling |
| 🔧 **Ops Agent** | Maintenance | Ticket triage, staff assignment, incident escalation |
| 🧹 **HSK Agent** | Housekeeping | Daily batch scheduling, checkout cleans, turndown, stayover |
| 💰 **Revenue Agent** | Pricing | Dynamic pricing, forecasting, event-driven yield management |

---

## 🚀 Quick Start

### Docker (recommended — 30 seconds)

```bash
git clone https://github.com/AnaVuko1/hotel-automation-engine.git
cd hotel-automation-engine
docker compose build
docker compose up
```

Open: **http://localhost:8000** · API docs: **http://localhost:8000/docs**

### Manual

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_demo.py       # 12 months of realistic data
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧠 Agent Architecture

```
                    ┌──────────────────────────────────┐
                    │       ORCHESTRATOR AGENT         │
                    │   routes · delegates · logs      │
                    └──────┬──────────┬───────────────┘
                           │          │
            ┌──────────────┤          ├──────────────┐
            │              │          │              │
       ┌────▼───┐    ┌────▼───┐ ┌────▼───┐    ┌────▼──────┐
       │ GUEST  │    │  OPS   │ │  HSK   │    │  REVENUE  │
       │ AGENT  │    │ AGENT  │ │ AGENT  │    │  AGENT    │
       └────┬───┘    └────┬───┘ └────┬───┘    └────┬──────┘
            │              │          │              │
       ┌────▼──────────────▼──────────▼──────────────▼──────┐
       │         PMS · Schema.org · Webhook Adapters        │
       └────────────────────────────────────────────────────┘
```

### How Agents Work

Every agent inherits from `BaseAgent` which provides:
- **Automatic logging** — every action is timestamped, logged with confidence score
- **Decision tracking** — each action is tagged as `auto`, `escalated`, `scheduled`, or `error`
- **Confidence scoring** — agents self-assess whether an action needs human review
- **Escalation triggers** — automatic handoff to human staff when confidence < threshold

### Key Agent Behaviors

**Guest Agent:**
- Auto-approves late checkout requests up to 2PM, escalates after
- Generates personalized upsell offers (room upgrade, spa, dining, late checkout)
- Sends welcome emails on check-in, feedback requests on check-out

**Ops Agent:**
- Triages maintenance priority based on category + keyword detection
- `"leak"`, `"flood"`, `"no power"` → auto‑elevated to HIGH priority
- `"incident"` type → immediate escalation to Manager-on-Duty
- Auto-assigns staff by category (plumbing → Plumber-on-Duty, HVAC → HVAC-Technician)

**HSK Agent:**
- Runs full daily batch in one call: checkout cleans → stayover → turndown
- Detects multi-night guests automatically for stayover scheduling
- Configurable priority per task type

**Revenue Agent:**
- Dynamic pricing: `final_price = base × occupancy_mult × season_mult × urgency_mult × event_mult`
- 4 independent multiplier factors
- Event-aware — local events (conferences, festivals) automatically boost prices

---

## 🔌 API Reference

### Agent System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/agents/execute` | Execute any agent action (routed by Orchestrator) |
| `GET` | `/api/v1/agents/status` | Overall system status |
| `GET` | `/api/v1/agents/recent` | Recent agent actions (last N) |

### Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/operations/maintenance` | Create maintenance task |
| `GET` | `/api/v1/operations/maintenance` | List maintenance tasks |
| `PATCH` | `/api/v1/operations/maintenance/{id}` | Update task status |
| `POST` | `/api/v1/operations/housekeeping` | Create housekeeping task |
| `GET` | `/api/v1/operations/housekeeping` | List housekeeping tasks |
| `PATCH` | `/api/v1/operations/housekeeping/{id}` | Update task status |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/analytics/metrics` | Dashboard KPIs (ADR, RevPAR, occupancy, etc.) |
| `GET` | `/api/v1/analytics/revenue-trend` | Monthly revenue breakdown |
| `GET` | `/api/v1/analytics/occupancy-trend` | Monthly occupancy trend |
| `GET` | `/api/v1/analytics/agent-performance` | Agent success rates & execution times |

### AI Agent Discovery (schema.org)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/agent-inventory/hotel` | Hotel JSON-LD |
| `GET` | `/api/v1/agent-inventory/rooms` | Room types JSON-LD |
| `GET` | `/api/v1/agent-inventory/availability` | Availability JSON-LD |
| `GET` | `/.well-known/ai-agent.json` | AI agent discovery manifest |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/webhooks/pms/booking-created` | PMS: new booking |
| `POST` | `/api/v1/webhooks/pms/booking-cancelled` | PMS: cancellation |
| `POST` | `/api/v1/webhooks/generic` | Generic event ingestion |

---

## 📊 Demo: One-Call Daily Batch

The engine is designed so a single API call triggers a full day of automation:

```bash
# Full daily ops batch
curl -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent":"hsk","action":"daily_batch","params":{"hotel_id":1}}'

# Dynamic pricing recalculation
curl -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent":"revenue","action":"pricing","params":{}}'

# Dashboard metrics
curl http://localhost:8000/api/v1/analytics/metrics?period_days=30
```

### Sample Dashboard Output

```json
{
  "occupancy_rate": 0.7845,
  "average_daily_rate": 187.50,
  "revpar": 147.20,
  "total_revenue": 284750.00,
  "direct_booking_rate": 0.6532,
  "ota_leakage": 18390.50,
  "ai_readiness_score": 82,
  "active_maintenance": 5,
  "pending_housekeeping": 8,
  "check_ins_today": 14,
  "check_outs_today": 11
}
```

---

## ⚙️ Architecture Details

### Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | FastAPI | Async HTTP + WebSocket |
| ORM | SQLAlchemy 2.0 (async) | Database abstraction |
| Agents | Custom Python classes | Modular, inheritable agent system |
| Pricing | Custom engine | 4-factor dynamic pricing model |
| AI Discovery | schema.org JSON-LD | AI agent discoverability |
| Validation | Pydantic v2 | Request/response schemas |
| Storage | SQLite (dev) / PostgreSQL (prod) | Data persistence |
| Infra | Docker · Compose | One-command deployment |

### Database Schema

```
Hotel (1) ──── RoomType (N) ──── Booking (N)
    │                              │
    └── PricingHistory (N)         └── GuestMessage (N)
    │
    ├── MaintenanceTask (N)
    ├── HousekeepingTask (N)
    └── LocalEvent (N)
```

### Agent Logging

Every agent action is persisted to `agent_logs` with:
- `agent_type`, `action`, `entity_type`, `entity_id`
- `input_data` / `output_data` (JSON)
- `decision` (auto / escalated / scheduled / error)
- `confidence` (0.0–1.0)
- `duration_ms`
- `created_at`

---

## 📈 Use Cases

### 1. Independent Hotel (50–200 rooms)
Replace manual front-desk tasks: automated check-in/out, upsell generation, housekeeping scheduling, maintenance ticket triage.

### 2. Boutique Hotel Group (multi-property)
Deploy per property with centralized analytics. Revenue agent adjusts pricing per location based on local events.

### 3. PMS Integration
Webhook endpoints accept booking events from any PMS. Agents respond: send confirmation, schedule cleaning, update pricing.

### 4. AI Agent Readiness
Schema.org JSON-LD endpoints make the hotel discoverable by AI agents. The `ai-agent.json` manifest describes capabilities for autonomous AI booking agents.

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run verification script
python scripts/verify.py
```

---

## 🎯 Roadmap

- [x] Multi-agent orchestration with logging & confidence scoring
- [x] 4 specialized sub-agents (Guest, Ops, HSK, Revenue)
- [x] Dynamic pricing engine (4-factor multiplier model)
- [x] Schema.org JSON-LD for AI agent discovery
- [x] Webhook integration layer
- [x] 12-month demo data seed
- [ ] PMS integrations (Mews, Opera, Protel adapters)
- [ ] WhatsApp / SMS messaging channel
- [ ] Real-time dashboard (WebSocket updates)
- [ ] Multi-property management
- [ ] ML-based demand forecasting

---

<div align="center">
<sub>MIT &mdash; hotel-automation-engine v1.0</sub>
</div>
