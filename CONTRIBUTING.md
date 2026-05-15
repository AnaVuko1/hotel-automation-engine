# Contributing to Hotel Automation Engine

Thank you for your interest in contributing! This project aims to make hotel operations automation accessible to independent hotels and boutique properties worldwide.

## Quick Start

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Commit with a clear message
6. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/hotel-automation-engine.git
cd hotel-automation-engine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Seed demo data
python scripts/seed_demo.py

# Run development server
uvicorn app.main:app --reload --port 8000
```

## Project Structure

```
app/
├── agents/          # AI agents (base, orchestrator, guest, ops, hsk, revenue)
├── adapters/        # External format adapters (schema.org JSON-LD)
├── routes/          # FastAPI route handlers
├── services/        # Business logic (pricing engine, etc.)
├── models.py        # SQLAlchemy database models
├── schemas.py       # Pydantic request/response schemas
├── config.py        # Configuration (pydantic-settings)
├── database.py      # Async SQLAlchemy setup
└── main.py          # FastAPI application entry point
scripts/
├── seed_demo.py     # Generate 12 months of realistic demo data
└── verify.py        # Verify installation and run smoke tests
tests/
└── test_engine.py   # Test suite
```

## Adding a New Agent

1. Create `app/agents/your_agent.py` extending `BaseAgent`
2. Implement `handle_*` methods for each action
3. Register in `OrchestratorAgent.agents` dict
4. Add route mapping in `OrchestratorAgent.handle_route`
5. Add tests in `tests/test_engine.py`

## Code Style

- Python 3.11+ with type hints
- Async/await throughout
- Pydantic v2 for schemas
- SQLAlchemy 2.0 async ORM
- Keep agents stateless — use the database for persistence

## Reporting Issues

- Use GitHub Issues
- Include: Python version, OS, steps to reproduce, expected vs actual behavior
- For security issues, please report privately (do not open public issues for vulnerabilities)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
