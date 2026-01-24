# Customer Service Agent - Copilot Instructions

## Project Overview

This project is building **rpcats** — a customer service AI agent for **Northern Oak** (e-commerce). The agent will automate ticket handling by following Standard Operating Procedures (SOPs) documented in the `sop/` directory.

## Architecture

```
customer-service-agent/
├── main.py              # Agent entry point
├── pyproject.toml       # uv package config (rpcats v0.1.0)
├── clients/             # API client modules
│   ├── __init__.py
│   └── gorgias.py       # Gorgias API client
├── analyse/             # Data analysis notebooks
│   └── gorgias-tickets-analysis.ipynb
├── data/                # Exported data files
└── sop/                 # Standard Operating Procedures (knowledge base)
    ├── order-delay.md
    ├── lost-in-transit.md
    ├── custom-charge.md
    ├── manage-quality-issue-resolution-using-gorgias-and-servicepoints.md
    ├── manage-wrong-order-issues-using-gorgias-and-servicepoints.md
    ├── manage-wrong-size-issues-in-customer-orders.md
    ├── order-alert-status.md
    ├── out-of-stock-triggered-by-leadership.md
    ├── out-of-stock-triggered-by-order-delay-and-dispute.md
    ├── proactive-follow-up-order-delay.md
    ├── process-damaged-item-claims-using-gorgias-and-servicepoints
    └── process-wrong-customization-issues-using-gorgias.md
```

## Dependencies

- `httpx` — HTTP client for API calls
- `python-dotenv` — Environment variable management
- `pandas` / `pyarrow` — Data analysis
- `matplotlib` — Visualization
- `ipykernel` — Jupyter notebook support

## Domain Context

### External Systems
The agent integrates with these platforms:
- **Gorgias** (`northenoak.gorgias.com`) - Customer support ticketing platform with macros
- **ServicePoints** - Order management, tracking, and dispute filing system
- **17Track** - Package tracking verification
- **ClickUp** - Dispute tracking
- **ChatGPT** - Message polishing before sending to customers

### Ticket Categories (Contact Reasons)
Reference `sop/` files for complete workflows:
| Issue Type | Key Macro | Resolution Priority |
|------------|-----------|---------------------|
| Order Delay | "Order Delay – Unassigned" | Provide stage updates, snooze 24h |
| Lost in Transit | "Lost in Transit" | File dispute → replacement → refund if needed |
| Wrong Order | "Wrong Order 1" | Verify → dispute → replacement/refund |
| Quality Issue | "Quality 1" | Request photos → dispute → replacement/refund |
| Wrong Size/Measurement | "Wrong Measurement 1" | Verify discrepancy → exchange/refund |
| Custom Charge | "Order Delay – Customer charge" | Free resend recommended |
| Out of Stock | Various | Triggered by order delay disputes |

### Standard Workflow Pattern
Most SOPs follow this structure:
1. **Read & classify** — Identify issue type from customer email, set Contact Reason dropdown
2. **Locate order** — Search ServicePoints by email, name, or order number
3. **Verify timeline** — Check shipping status in ServicePoints, cross-reference 17Track
4. **File dispute** (if applicable) — Track in ClickUp Dispute Tracker
5. **Apply macro** — Use appropriate Gorgias macro, polish with ChatGPT
6. **Snooze & assign** — Typically 24h snooze for follow-up

### Resolution Priority
1. **Replacement** (preferred) — Approved by supplier or processed internally via Amor
2. **Refund** (escalation) — Requires approval from Vincent or Leadership team

## Development Setup

```powershell
uv sync          # Install dependencies
uv run main.py   # Run the agent
```

Environment variables (`.env`):
- Configure API credentials for Gorgias and other integrations

## Code Conventions

- **Python 3.10+** with `uv` for package management
- Reference SOPs by filename when implementing ticket handlers (e.g., `sop/lost-in-transit.md`)
- SOP files are markdown exports from Guidde video tutorials — extract step logic, ignore UI screenshots

## Key Files to Reference

- [sop/order-delay.md](sop/order-delay.md) — Core example of the standard workflow pattern
- [sop/lost-in-transit.md](sop/lost-in-transit.md) — Dispute filing + replacement flow
- [sop/manage-quality-issue-resolution-using-gorgias-and-servicepoints.md](sop/manage-quality-issue-resolution-using-gorgias-and-servicepoints.md) — Complex multi-step dispute handling
