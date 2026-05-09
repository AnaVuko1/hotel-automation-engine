![banner](assets/banner.jpg)

<div align="center">

# hotel-automation-engine

**Multi-agent AI system for end-to-end hotel operations automation**

![Python](https://img.shields.io/badge/Python-0d1117?style=flat-square&logo=python&logoColor=6EE7B7)
![FastAPI](https://img.shields.io/badge/FastAPI-0d1117?style=flat-square&logo=fastapi&logoColor=6EE7B7)
![Docker](https://img.shields.io/badge/Docker-0d1117?style=flat-square&logo=docker&logoColor=6EE7B7)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-0d1117?style=flat-square&logo=postgresql&logoColor=6EE7B7)
![Redis](https://img.shields.io/badge/Redis-0d1117?style=flat-square&logo=redis&logoColor=6EE7B7)

</div>

---

## overview

A production-grade automation engine that orchestrates AI agents across hotel operations — from guest communication and check-in flows to housekeeping scheduling, maintenance ticketing, and real-time staff coordination.

Designed for properties that want to reduce manual overhead without replacing their existing PMS.

## architecture

```
┌─────────────────────────────────────────────────────┐
│                 orchestrator agent                  │
│          routes tasks · manages state               │
└──────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼──────┐
  │ guest  │ │  ops   │ │  hsk   │ │ revenue  │
  │ agent  │ │ agent  │ │ agent  │ │  agent   │
  └────┬───┘ └───┬────┘ └───┬────┘ └───┬──────┘
       │          │          │          │
  ┌────▼──────────▼──────────▼──────────▼──────┐
  │          PMS · CRM · Messaging APIs         │
  └─────────────────────────────────────────────┘
```

## key features

- **Automated guest flows** — check-in/check-out, upsell triggers, late checkout handling
- **Ops coordination** — real-time task routing between housekeeping, maintenance, front desk
- **PMS integrations** — Mews, Opera, Protel adapter layer
- **AI-powered triage** — incoming requests classified and routed without human intervention
- **Escalation logic** — knows when to loop in a human and how to hand off context
- **Multi-channel** — WhatsApp, email, booking platform webhooks

## stack

| Layer | Technology |
|---|---|
| Orchestration | Python · FastAPI · Celery |
| AI | Claude 3.5 / GPT-4o · LangChain tool use |
| Storage | PostgreSQL · Redis |
| Infra | Docker · Traefik · Linux VPS |
| Integrations | REST · Webhook adapters · SMTP |

## results

> Deployed across 4 properties. Average **47% reduction** in front-desk manual tasks within 30 days.

---

<div align="center">
<sub>built by <a href="https://github.com/AnaVuko1">@AnaVuko1</a> · inquiries: aeth-lab@pm.me</sub>
</div>
