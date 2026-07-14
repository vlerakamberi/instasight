# InstaSight — Instagram Analytics Platform

AI-assisted analytics platform built for a real client (dental clinic),
identifying data quality issues and generating actionable insights from
Instagram performance data.

## Key Results
- Identified a **685-day gap** in posting history through automated quality checks
- Synced **23 posts**, tracking **993 followers** and **1.64% engagement rate**
- Built **10+ test modules** covering database, metrics, and API reliability

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | Python, Streamlit |
| Database | SQLite |
| Data Source | Instagram Graph API |
| AI Layer | Anthropic Claude API |

## Architecture
```
instasight/
├── app/
│   ├── api/          — Instagram Graph API client
│   ├── analytics/    — sync, metrics, monitoring, and trend analysis
│   ├── ai/           — Claude-powered strategy generation and benchmarking
│   └── dashboard/    — Streamlit dashboard UI
└── tests/            — unit and integration tests
```

## Setup
```bash
git clone https://github.com/vlerakamberi/instasight.git
cd instasight
pip install -r requirements.txt
```

> **Note:** Add your API credentials to a `.env` file (see `.env.example`)

```bash
streamlit run main.py
```

## Testing
```bash
pytest tests/
```
