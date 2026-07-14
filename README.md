# InstaSight — Instagram Analytics Platform

AI-assisted analytics platform built for a real client (dental clinic), 
identifying data quality issues and generating actionable insights from 
Instagram performance data.

## Key Results
- Identified a 685-day gap in posting history through automated quality checks
- Synced 23 posts, tracking 993 followers and 1.64% engagement rate
- Built 10+ test modules covering database, metrics, and API reliability

## Tech Stack
- Python, Streamlit
- SQLite
- Instagram Graph API
- Anthropic Claude API (AI analysis layer, grounded in verified DB records)

## Architecture
- `app/api/` — Instagram Graph API client
- `app/analytics/` — sync, metrics, monitoring, and trend analysis
- `app/ai/` — Claude-powered strategy generation and benchmarking
- `app/dashboard/` — Streamlit dashboard UI
- `tests/` — unit and integration tests

## Setup
\`\`\`bash
git clone https://github.com/vlerakamberi/instasight.git
cd instasight
pip install -r requirements.txt
# Add your API credentials to a .env file (see .env.example)
streamlit run main.py
\`\`\`

## Testing
\`\`\`bash
pytest tests/
\`\`\`
