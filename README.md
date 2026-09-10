# NovaDesk AI Operations Engine

An AI-powered customer dispute resolution system for a fictional SaaS company.

## Problem
Support teams manually investigate billing disputes by combining customer messages, payment records, and company policies. This is slow, error-prone, and difficult to scale.

## Solution
An AI system that:
1. Ingests a customer support case
2. Retrieves relevant company policy using a retrieval layer
3. Queries the database for evidence such as payments, subscriptions, and customer records
4. Generates a structured decision such as refund, escalate, or investigate
5. Applies guardrails before any action is taken

## Architecture
- FastAPI — API layer
- PostgreSQL + pgvector — relational and vector storage
- SQLAlchemy — ORM and database access
- Groq API — LLM inference
- Docker — containerized local environment

## Data Model
- customers — customer account records
- subscriptions — subscription lifecycle and current status
- payments — payment history and settlement status
- invoices — invoice records and billing activity
- support_cases — customer disputes and issue descriptions

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | API status message |
| GET | /health | Database connectivity check |
| GET | /customers/ | List all customers |
| GET | /customers/{id} | Get one customer |
| GET | /payments/ | List all payments |
| GET | /subscriptions/ | List all subscriptions |
| GET | /support-cases/ | List all support cases |

## Setup
```bash
docker-compose up -d
python -m scripts.create_tables
python -m scripts.load_data
uvicorn app.main:app --reload
```

## Environment
Copy the sample environment file and set your local values:

```bash
copy .env.example .env
```

## Testing
```bash
pytest tests/ -v
```

## Roadmap
- ✅ Day 1 — Backend and database foundation
- ✅ Day 2 — Service layer and production-focused structure
- ☐ Day 3 — LLM extraction workflow
- ☐ Day 4 — Retrieval and policy grounding
- ☐ Day 5 — Evaluation pipeline
- ☐ Day 6 — Workflow automation
- ☐ Day 7 — Production hardening
- ☐ Day 8 — Deployment

## Production Notes
This project already includes:
- structured service-layer separation
- custom not-found and validation exceptions
- database health checks
- JSON logging
- environment configuration template
- test coverage for key API routes

## Final status
The application is structured for a more maintainable production workflow and is validated with automated API tests.
