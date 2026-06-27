# InstaSight — Technical Documentation

> Instagram Business analytics, AI strategy, and automated monitoring for the dental clinic **Dental-B** (`@dentalb_ku`).

---

## Table of Contents

1. [Project Overview & Purpose](#1-project-overview--purpose)
2. [Architecture](#2-architecture)
3. [Modules & Functions](#3-modules--functions)
4. [Database Schema](#4-database-schema)
5. [API Integrations](#5-api-integrations)
6. [Installation & Running](#6-installation--running)
7. [Running Tests](#7-running-tests)
8. [Dashboard Pages](#8-dashboard-pages)
9. [Configuration Reference](#9-configuration-reference)

---

## 1. Project Overview & Purpose

InstaSight is a Python application that turns raw Instagram Graph API data into actionable growth guidance for a small dental clinic. It:

- **Syncs** profile, posts, and per-post insights from the Instagram Graph API into a local SQLite database.
- **Computes** analytics metrics (engagement rate, posting frequency, best posting day, content-type performance, top posts).
- **Generates** AI output via the Anthropic Claude API: a long-form growth strategy, a data-backed performance diagnosis, and a concrete weekly action plan.
- **Monitors** the account daily, capturing performance snapshots and raising alerts on engagement drops, posting inactivity, and engagement spikes.
- **Notifies** via Gmail SMTP (weekly plan emails and alert digests).
- **Visualizes** everything in a multi-page Streamlit dashboard with Plotly charts.

The single target account is hard-coded as `ACCOUNT_ID = "17841409576371357"` in the dashboard and scheduler.

### Tech stack

| Concern | Technology |
| --- | --- |
| Language | Python 3 |
| Data store | SQLite (`data/instasight.db`) |
| External APIs | Instagram Graph API (Meta), Anthropic Claude |
| Dashboard | Streamlit + Plotly |
| AI | `anthropic` SDK (`claude-sonnet-4-6`) |
| Email | Gmail SMTP (`smtplib`) |
| Scheduling | `schedule` + `threading` |
| Config | `.env` via `python-dotenv` |
| Tests | `pytest` |

---

## 1.1 Problem Statement

Small and medium businesses in the Albanian-speaking market
(North Macedonia, Kosovo, Albania, diaspora) face a critical gap:
professional digital marketing consultants charge €500-2,000/month
— far beyond the budget of a local dental clinic with under 1,000
followers. Generic AI tools like ChatGPT cannot help because they
have no access to the business's actual Instagram data, historical
performance, or account-specific patterns.

InstaSight bridges this gap by providing the same quality of
data-driven analysis that a senior growth marketer would deliver,
grounded entirely in the business's own real data.

---

## 1.2 Design Decisions

### Why Performance Advisor instead of a generic AI assistant

During development and testing with Dental-B, it became clear that:

1. Generic AI advice is a commodity — ChatGPT, Canva, Buffer,
   and Later all generate content suggestions.
2. The real value gap is in diagnosis, not content creation.
   A business owner does not need another caption — they need
   to understand WHY their engagement is 1.68% instead of 4-6%,
   and WHAT specific actions to take based on their own data.

The system was therefore designed around two complementary
AI features:
- Performance Advisor — short, focused diagnosis for regular use
- AI Strategy — deep one-time audit with full recommendations

Both are grounded exclusively in real account data from the
Instagram Graph API, making every output specific to the
business being analyzed.

---

## 1.3 Case Study — Dental-B (@dentalb_ku)

### Business profile
- **Name:** Dental-B, Kumanovo, North Macedonia
- **Instagram:** @dentalb_ku
- **Followers:** 999 (as of June 2026)
- **Target audience:** Albanian-speaking patients across
  North Macedonia, Kosovo, Albania, and diaspora

### Key findings from InstaSight analysis

| Metric | Value | Benchmark | Status |
|--------|-------|-----------|--------|
| Avg engagement rate | 1.68% | 4-6% (nano accounts) | Below potential |
| Posts per week | 0.07 | 3-5/week | Critical gap |
| Longest posting gap | 685 days | — | Account dormancy |
| Reels posted | 0 | 40% of content mix | Missing format |
| Comments per post | ~0 | 3-8 | Passive audience |

### System diagnosis
The Performance Advisor identified that Dental-B has a functional
audience (1.68% engagement proves people respond when content
appears) but posts so infrequently that Instagram's algorithm
has stopped distributing the content.

The AI Strategy identified that existing hashtags were targeting
English-speaking audiences and dentists in Turkey rather than
Albanian speakers in the region — a critical error costing the
account organic reach.

### Automated monitoring
The monitoring engine captures daily performance snapshots.
A Windows Task Scheduler job runs scripts/run_monitoring.py
every day at 08:00, independently of whether the dashboard
is open. Alert emails are sent automatically when engagement
drops more than 20% or posting inactivity exceeds 7 days.

### Value delivered
InstaSight replaced the need for a paid marketing consultant
for performance analysis. The system provided:
- A complete hashtag framework specific to the Albanian dental market
- Identification of a 685-day posting gap causing algorithm penalization
- A 30-day activation plan grounded in the account's real historical data
- Automated daily monitoring with email alerts

---

## 2. Architecture

### Text-based architecture diagram

```
                        ┌──────────────────────────────────────────────┐
                        │              External Services               │
                        │                                              │
                        │   Instagram Graph API      Anthropic Claude  │
                        │   (graph.facebook.com)     (claude-sonnet)   │
                        │            ▲                      ▲           │
                        └────────────┼──────────────────────┼──────────┘
                                     │                      │
                     ┌───────────────┘                      └───────────────┐
                     │                                                       │
            ┌────────┴─────────┐                               ┌─────────────┴────────────┐
            │  app/api          │                               │  app/ai                  │
            │  meta_client.py   │                               │  strategy_generator.py   │
            │  (+ retry.py)     │                               │  performance_advisor.py  │
            └────────┬──────────┘                               │  weekly_planner.py       │
                     │                                          │  benchmarks.py           │
                     │ profile / media / insights               └─────────────┬────────────┘
                     ▼                                                         │ prompt context
            ┌────────────────────┐                                            │
            │ app/analytics       │                                           │
            │ sync_service.py     │──── writes ──┐                            │
            └────────────────────┘               │                           │
                                                  ▼                           │
                                       ┌─────────────────────┐                │
                                       │  app/database        │               │
                                       │  connection.py       │◀──────────────┘
                                       │  schema.sql          │   reads (build_report)
                                       │  data/instasight.db  │
                                       └──────────┬───────────┘
                                                  │ reads
                     ┌────────────────────────────┼─────────────────────────────┐
                     ▼                             ▼                             ▼
          ┌────────────────────┐      ┌────────────────────┐        ┌────────────────────┐
          │ analytics/metrics  │      │ analytics/monitoring│        │ analytics/          │
          │ analytics/analysis │      │ analytics/scheduler │        │ trend_analysis.py   │
          │ analytics/report_  │      │ (daemon thread)     │        └────────────────────┘
          │   builder.py       │      └─────────┬───────────┘
          └─────────┬──────────┘                │ alerts
                    │                            ▼
                    │                 ┌────────────────────────┐
                    │                 │ app/notifications       │
                    │                 │ email_sender.py (Gmail) │
                    │                 └────────────────────────┘
                    ▼
          ┌────────────────────────────────────────────┐
          │ app/dashboard/streamlit_app.py              │
          │ Overview · Post Analysis · Trends ·         │
          │ AI Strategy · Performance Advisor           │
          └────────────────────────────────────────────┘
```

### Data flow

1. `MetaClient` fetches profile, recent media, and per-post insights from the Graph API (with retry).
2. `sync_account_data()` upserts accounts/posts and inserts insight snapshots into SQLite.
3. `metrics.py` / `analysis.py` / `report_builder.py` read the DB and compute analytics.
4. `report_builder.build_prompt_context()` formats the analytics into a plain-text context for the LLM.
5. `app/ai/*` send that context to Claude and return generated text.
6. `monitoring.py` captures daily snapshots and compares them to raise alerts; `scheduler.py` runs this on a background thread and emails alerts.
7. `streamlit_app.py` renders all of the above as interactive pages.

### Directory layout

```
InstaSight/
├── main.py                         # CLI entry point: init DB + sync once
├── requirements.txt
├── data/
│   ├── instasight.db               # SQLite database (generated)
│   └── app.log                     # Rotating application log
├── scripts/
│   └── run_monitoring.py           # Standalone monitoring runner
├── app/
│   ├── config.py                   # .env loading + Settings dataclass
│   ├── retry.py                    # Exponential-backoff retry helper
│   ├── utils_logger.py             # Logger factory (console + data/app.log)
│   ├── api/
│   │   └── meta_client.py          # Instagram Graph API client
│   ├── database/
│   │   ├── connection.py           # get_connection() / init_db()
│   │   └── schema.sql              # Table & index definitions
│   ├── analytics/
│   │   ├── sync_service.py         # API → DB sync pipeline
│   │   ├── metrics.py              # Metric calculations
│   │   ├── analysis.py             # Aggregated analysis + insights
│   │   ├── report_builder.py       # LLM-ready report + prompt context
│   │   ├── monitoring.py           # Snapshots + alert generation
│   │   ├── scheduler.py            # Background daily scheduler
│   │   └── trend_analysis.py       # Historical trend summaries
│   ├── ai/
│   │   ├── benchmarks.py           # Shared benchmark prompt block
│   │   ├── strategy_generator.py   # Long-form growth strategy
│   │   ├── performance_advisor.py  # Data-backed diagnosis
│   │   └── weekly_planner.py       # Concrete weekly plan
│   ├── notifications/
│   │   └── email_sender.py         # Gmail SMTP (plan + alert emails)
│   └── dashboard/
│       └── streamlit_app.py        # Streamlit UI
└── tests/                          # pytest suite + standalone scripts
```

---

## 3. Modules & Functions

### `app/config.py`

| Symbol | Description |
| --- | --- |
| `Settings` (dataclass) | Holds `meta_app_id`, `meta_app_secret`, `meta_graph_version`, `instagram_account_id`, `instagram_access_token`, `redirect_uri`, `anthropic_api_key`, `gmail_address`, `gmail_app_password`. |
| `load_settings() -> Settings` | Loads `.env`, builds `Settings`, and raises `ValueError` if any required key is missing. **Required:** Meta app id/secret, Instagram account id/token, redirect URI, Anthropic API key. Gmail keys are optional. |

### `app/retry.py`

| Symbol | Description |
| --- | --- |
| `run_with_retry(operation, operation_name, logger, max_attempts=3, base_delay_seconds=1.0)` | Runs `operation()` with exponential backoff (`delay = base_delay * 2^(attempt-1)`). Logs warnings on retry, error on final failure, and re-raises the last exception. |

### `app/utils_logger.py`

| Symbol | Description |
| --- | --- |
| `setup_logger(name="instasight") -> logging.Logger` | Returns a logger writing to both console and `data/app.log` (UTF-8). Idempotent — re-uses existing handlers. |

### `app/api/meta_client.py`

| Symbol | Description |
| --- | --- |
| `MetaClientError(Exception)` | Raised on invalid/unavailable Meta data. |
| `MetaClient()` | Builds base URL from `meta_graph_version` and loads access token + account id from settings. |
| `get_profile_info() -> Dict` | Retried fetch + validation of profile. Returns `instagram_account_id`, `username`, `followers_count`, `media_count`, `biography`. |
| `get_recent_media() -> List[Dict]` | Retried fetch of up to 20 recent posts (`post_id`, `caption`, `media_type`, `timestamp`, `permalink`). |
| `get_media_insights(media_id) -> Dict` | Retried fetch of `like_count`/`comments_count` for a post; returns `likes_count`, `comments_count`, `shares`, `saves`, `reach`, `impressions` (last four are `0`). |
| `_fetch_profile_info()` | Tries `username,followers_count,media_count`; falls back to `username,followers_count` if the API returns an error. |
| `_fetch_media_insights(media_id)` | On HTTP 400 or API error, logs a warning and returns zeroed insights instead of raising. |
| `_validate_profile(profile)` | Ensures required profile keys + non-empty username. |

### `app/database/connection.py`

| Symbol | Description |
| --- | --- |
| `DB_PATH` | `data/instasight.db` under project root. |
| `get_connection() -> sqlite3.Connection` | Opens a connection with `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`. Creates the `data/` directory if needed. |
| `init_db()` | Executes `schema.sql` (all `CREATE ... IF NOT EXISTS`), safe to run repeatedly. |

### `app/analytics/sync_service.py`

| Symbol | Description |
| --- | --- |
| `sync_account_data(client: MetaClient) -> Dict` | Full pipeline: `init_db()` → profile → upsert account → recent media → insert new posts (skips existing) → per-post insights (errors on one post are logged and skipped). Returns `{posts_synced, insights_synced, account}`. |

### `app/analytics/metrics.py`

All functions read from SQLite and log results. Engagement rate formula: `(likes + comments) / followers * 100`.

| Function | Returns |
| --- | --- |
| `engagement_rate(post_id)` | Dict with the post's latest engagement rate. |
| `avg_engagement_rate(account_id)` | Dict: `followers_count`, `post_count`, `avg_engagement_rate` (mean of per-post rates). |
| `top_performing_posts(account_id, limit=5)` | List of posts sorted by engagement rate descending. |
| `posting_frequency(account_id)` | Dict: `post_count`, `weeks_span`, `posts_per_week`. |
| `best_posting_day(account_id)` | Dict: best weekday by average engagement. |
| `content_type_performance(account_id)` | List per media type: `post_count`, `avg_engagement_rate`. |

### `app/analytics/analysis.py`

| Function | Returns |
| --- | --- |
| `analyze_account(account_id)` | Combines all metrics into one dict (`account`, `avg_engagement_rate`, `top_performing_posts`, `posting_frequency`, `best_posting_day`, `content_type_performance`) and appends `growth_insights`. |
| `generate_growth_insights(analysis)` | List of human-readable observations derived from the analysis. |

### `app/analytics/report_builder.py`

| Function | Returns |
| --- | --- |
| `build_report(account_id)` | LLM-ready dict: `account_summary`, `posting_frequency_detail`, `best_posting_day`, `top_posts`, `posting_timeline`, `media_type_breakdown`, `patterns`, `growth_insights`, `generated_at`. |
| `build_prompt_context(report)` | Plain-text prompt context grounded strictly in real DB metrics (followers, engagement, frequency, top posts, posting timeline with gaps, media breakdown, insights). |

### `app/analytics/monitoring.py`

| Function | Description |
| --- | --- |
| `save_daily_snapshot(account_id)` | Computes today's metrics + `posts_this_week`, `INSERT OR REPLACE` into `performance_snapshots`. Returns the snapshot dict. |
| `check_and_generate_alerts(account_id)` | Compares the two latest snapshots; raises `engagement_drop` (>20% drop), `posting_inactivity` (0 posts in 7 days), `engagement_spike` (>30% rise). Inserts into `alerts`, returns the list. |
| `run_daily_monitoring(account_id)` | Orchestrates snapshot + alerts. Returns `{account_id, snapshot, alerts, alerts_count, ran_at}`. |

Thresholds: `ENGAGEMENT_DROP_THRESHOLD = 20.0`, `ENGAGEMENT_SPIKE_THRESHOLD = 30.0`.

### `app/analytics/scheduler.py`

| Function | Description |
| --- | --- |
| `run_monitoring_job()` | Runs `run_daily_monitoring()` and emails alerts via `send_alert_email()` when any exist. |
| `start_scheduler()` | Warns if Gmail unconfigured, schedules the job every 24h, runs it once immediately, and starts a daemon thread looping `schedule.run_pending()`. |
| `get_scheduler_status()` | Returns `is_running`, `next_run`, `account_id`, `job_count`. |

### `app/analytics/trend_analysis.py`

| Function | Description |
| --- | --- |
| `get_performance_trend(account_id, days=30)` | Returns snapshots within the window (oldest first): `snapshot_date`, `followers_count`, `avg_engagement_rate`, `posts_this_week`, `top_media_type`. |
| `get_trend_summary(account_id, days=30)` | Needs ≥2 snapshots. Returns `has_data`, engagement start/end/change, followers start/end/change, `avg_posts_per_week`, `trend_direction` (`up`/`down`/`stable`), date bounds, counts. Otherwise `{has_data: False, message}`. |

### `app/ai/benchmarks.py`

| Symbol | Description |
| --- | --- |
| `BENCHMARK_CONTEXT` | Shared verified Instagram benchmark text (engagement rates, content strategy, posting frequency, hashtags, Albanian dental market context) appended to AI system prompts. Ends with "Respond in English." |

### `app/ai/strategy_generator.py`

| Symbol | Description |
| --- | --- |
| `MODEL = "claude-sonnet-4-6"` | Model used. |
| `SYSTEM_PROMPT` | "Senior Instagram marketing consultant" persona + `BENCHMARK_CONTEXT`. |
| `generate_strategy(account_id) -> Dict` | Builds report + context, **streams** the response (`client.messages.stream(...).get_final_text()`, `max_tokens=4096`). Returns `{account_id, username, strategy, generated_at}`. |

### `app/ai/performance_advisor.py`

| Symbol | Description |
| --- | --- |
| `MODEL` / `SYSTEM_PROMPT` | "Senior Instagram performance analyst"; strict sections (Diagnosis, Why, 3 Actions, What to Watch), Albanian output. |
| `generate_performance_advice(account_id) -> Dict` | Builds a diagnosis context, **streams** the response (`max_tokens=2048`). Returns `{account_id, username, advice, metrics_snapshot, generated_at}`. |

### `app/ai/weekly_planner.py`

| Symbol | Description |
| --- | --- |
| `MODEL` / `SYSTEM_PROMPT` | "Weekly Instagram growth coach"; day-by-day plan with captions, hashtags, timing, visuals, expected engagement + `BENCHMARK_CONTEXT`. |
| `coming_week_bounds(today=None) -> (Monday, Sunday)` | Date bounds for the coming week. |
| `generate_weekly_plan(account_id) -> Dict` | Builds report + pattern context, calls Claude (`messages.create`, `max_tokens=4096`). Returns `{account_id, username, week_start, week_end, plan, generated_at}`. |

> Note: the weekly planner is currently not surfaced as a dashboard page (its page is commented out) but the module remains functional and is used by `send_weekly_plan_email`.

### `app/notifications/email_sender.py`

| Function | Description |
| --- | --- |
| `send_weekly_plan_email(account_id, recipient_email, plan=None)` | Renders the weekly plan (markdown → HTML) and sends via Gmail SMTP. Reuses a pre-generated `plan` to avoid a second Claude call. Returns `bool`. |
| `send_alert_email(account_id, alerts)` | Renders an HTML alert digest with color-coded badges and sends to the configured Gmail address. Returns `bool`. |

SMTP: `smtp.gmail.com:587` with STARTTLS.

### `main.py`

| Function | Description |
| --- | --- |
| `main()` | Initializes the DB and runs a single `sync_account_data(MetaClient())` pass. CLI entry point. |

### `scripts/run_monitoring.py`

Standalone runner: `init_db()` → `run_daily_monitoring(ACCOUNT_ID)` → prints alert count → `send_alert_email()` when alerts exist.

---

## 4. Database Schema

SQLite file: `data/instasight.db`. Defined in `app/database/schema.sql`.

### `accounts`
| Column | Type | Notes |
| --- | --- | --- |
| `id` | TEXT | Primary key (Instagram account id) |
| `username` | TEXT | NOT NULL |
| `followers_count` | INTEGER | default 0 |
| `media_count` | INTEGER | default 0 |
| `biography` | TEXT | |
| `synced_at` | TIMESTAMP | default `CURRENT_TIMESTAMP` |

### `posts`
| Column | Type | Notes |
| --- | --- | --- |
| `id` | TEXT | Primary key (media id) |
| `account_id` | TEXT | NOT NULL, FK → `accounts(id)` |
| `caption` | TEXT | |
| `media_type` | TEXT | e.g. IMAGE / VIDEO / CAROUSEL_ALBUM |
| `timestamp` | TIMESTAMP | post time |
| `permalink` | TEXT | |

### `insights`
| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | PK, autoincrement |
| `post_id` | TEXT | NOT NULL, FK → `posts(id)` |
| `likes_count`, `comments_count`, `shares`, `saves`, `reach`, `impressions` | INTEGER | default 0 |
| `synced_at` | TIMESTAMP | default `CURRENT_TIMESTAMP` (each sync inserts a new snapshot) |

### `performance_snapshots`
| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | PK, autoincrement |
| `account_id` | TEXT | NOT NULL, FK → `accounts(id)` |
| `snapshot_date` | DATE | NOT NULL |
| `followers_count` | INTEGER | default 0 |
| `avg_engagement_rate` | REAL | default 0.0 |
| `posts_count` | INTEGER | default 0 |
| `posts_this_week` | INTEGER | default 0 |
| `top_media_type` | TEXT | |
| `captured_at` | TIMESTAMP | default `CURRENT_TIMESTAMP` |
| | | `UNIQUE(account_id, snapshot_date)` |

### `alerts`
| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | PK, autoincrement |
| `account_id` | TEXT | NOT NULL, FK → `accounts(id)` |
| `alert_type` | TEXT | NOT NULL (`engagement_drop`, `posting_inactivity`, `engagement_spike`) |
| `message` | TEXT | NOT NULL |
| `metric_value`, `metric_previous` | REAL | |
| `sent_at` | TIMESTAMP | default `CURRENT_TIMESTAMP` |
| `email_sent` | INTEGER | default 0 |

### Indexes
- `idx_posts_account_id` on `posts(account_id)`
- `idx_insights_post_id` on `insights(post_id)`
- `idx_snapshots_account_date` on `performance_snapshots(account_id, snapshot_date)`
- `idx_alerts_account_id` on `alerts(account_id)`

---

## 5. API Integrations

### Instagram Graph API (Meta)
- **Base URL:** `https://graph.facebook.com/{META_GRAPH_VERSION}` (default `v18.0`).
- **Auth:** `access_token` query param on every request (`INSTAGRAM_ACCESS_TOKEN`).
- **Endpoints used:**
  - `GET /{account_id}?fields=username,followers_count,media_count` (with fallback to `username,followers_count`).
  - `GET /{account_id}/media?fields=id,caption,media_type,timestamp,permalink&limit=20`.
  - `GET /{media_id}?fields=like_count,comments_count` (per-post insights via media object fields).
- **Resilience:** all calls go through `run_with_retry` (3 attempts, exponential backoff). HTTP 400 or API error on insights returns zeros rather than failing the whole sync.

### Anthropic Claude
- **SDK:** `anthropic`, model `claude-sonnet-4-6`.
- **Auth:** `ANTHROPIC_API_KEY`.
- **Usage:**
  - Strategy + Performance Advisor use **streaming** (`client.messages.stream(...)`).
  - Weekly planner uses non-streaming `client.messages.create(...)`.
  - All prompts are grounded in `build_prompt_context()` output plus `BENCHMARK_CONTEXT`.

### Gmail SMTP
- **Server:** `smtp.gmail.com:587` (STARTTLS).
- **Auth:** `GMAIL_ADDRESS` + `GMAIL_APP_PASSWORD` (Gmail App Password, not the account password).
- **Emails:** weekly plan (HTML) and alert digests (HTML + plain-text alternative).

---

## 6. Installation & Running

### Prerequisites
- Python 3.10+
- A Meta/Instagram Business account with a Graph API access token
- An Anthropic API key
- (Optional) Gmail account with an App Password for email features

### Setup

```bash
# 1. Clone and enter the project
cd InstaSight

# 2. (Recommended) create a virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Configure `.env`

Create a `.env` file in the project root:

```env
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_GRAPH_VERSION=v18.0
INSTAGRAM_ACCOUNT_ID=17841409576371357
INSTAGRAM_ACCESS_TOKEN=your_long_lived_token
REDIRECT_URI=https://localhost/
ANTHROPIC_API_KEY=sk-ant-...
# Optional (required only for email features)
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
```

### Initialize the database & run a first sync

```bash
python main.py
```

This runs `init_db()` and a single `sync_account_data()` pass, creating `data/instasight.db`.

### Launch the dashboard

```bash
streamlit run app/dashboard/streamlit_app.py
```

The dashboard starts the background monitoring scheduler automatically on first load. Use **Sync Data** in the sidebar to refresh metrics.

### Run monitoring manually (without the dashboard)

```bash
python scripts/run_monitoring.py
```

---

## 7. Running Tests

The suite uses `pytest`. Some tests require live credentials or a populated database and skip automatically when prerequisites are missing.

```bash
# Run the full suite quietly
python -m pytest tests/ -q

# Run a single file
python -m pytest tests/test_metrics.py -q
```

### Test files

| File | Scope |
| --- | --- |
| `tests/test_settings.py` | `.env` loading / required-key validation. |
| `tests/test_db.py` | Schema creation via `init_db()`. |
| `tests/test_retry.py` | `run_with_retry` backoff behavior. |
| `tests/test_metrics.py` | Each metric function in `metrics.py`. |
| `tests/test_analysis.py` | `analyze_account` / `generate_growth_insights`. |
| `tests/test_report_builder.py` | `build_report` / `build_prompt_context`. |
| `tests/test_monitoring.py` | `monitoring.py` + `trend_analysis.py`. **Skips entirely if `data/instasight.db` is missing.** |
| `tests/test_strategy_generator.py` | `generate_strategy` (needs Anthropic key). |
| `tests/test_weekly_planner.py` | `generate_weekly_plan` (needs Anthropic key). |
| `tests/test_email_sender.py` | `send_weekly_plan_email` (needs Gmail credentials). |
| `tests/test_real_api.py` | Standalone (not pytest) live Graph API connectivity script: `python tests/test_real_api.py`. |

> Notes: tests that call external services (Anthropic, Gmail, Graph API) consume real quota/credentials. Run the offline tests (`test_db`, `test_retry`, `test_metrics`, `test_analysis`, `test_report_builder`, `test_monitoring`) for fast local verification.

---

## 8. Dashboard Pages

Navigation lives in the sidebar (`PAGES = ("Overview", "Post Analysis", "Trends", "AI Strategy", "Performance Advisor")`). The sidebar also shows the account box, **Sync Data** / **Generate Strategy** buttons, monitoring status, and a **Run Check Now** button.

### Overview
- Four KPI cards: Followers, Engagement Rate (with good/low context), Posts Synced, Posts/Week.
- Engagement-rate-per-post line chart with an average reference line.
- Top-5-posts-by-engagement horizontal bar chart.
- Post details data table.
- Recent Alerts list (last 5 alerts from the DB).

### Post Analysis
- Content and timing insights for the account.
- Metric cards (avg engagement, posting frequency, best day) and content-type performance breakdown.

### Trends
- Time-period selector (Last 7 / 30 / 90 days).
- If <2 snapshots: an info message explaining how to build trend history.
- KPI cards: Engagement Trend (with direction icon), Followers Change, Avg Posts/Week, Data Points.
- Engagement-rate-over-time line chart and posts-per-week bar chart (from `performance_snapshots`).

### AI Strategy
- Account snapshot card.
- **Generate Strategy** button (or triggered from the sidebar). Streams the Claude response token-by-token into the page, then stores it in `st.session_state["strategy"]`.
- Generated strategy displayed in a styled box with a copy confirmation.

### Performance Advisor
- KPI cards: Avg Engagement, Posts/Week, Best Day, Best Format.
- **Analyze Performance** button builds a diagnosis context and streams the Claude response live, storing it in `st.session_state["performance_advice"]`.
- Re-analyze button clears state to regenerate.

---

## 9. Configuration Reference

| Env var | Required | Purpose |
| --- | --- | --- |
| `META_APP_ID` | Yes | Meta app identifier. |
| `META_APP_SECRET` | Yes | Meta app secret. |
| `META_GRAPH_VERSION` | No (default `v18.0`) | Graph API version. |
| `INSTAGRAM_ACCOUNT_ID` | Yes | Target IG Business account id. |
| `INSTAGRAM_ACCESS_TOKEN` | Yes | Long-lived Graph API token. |
| `REDIRECT_URI` | Yes | OAuth redirect URI. |
| `ANTHROPIC_API_KEY` | Yes | Claude API access. |
| `GMAIL_ADDRESS` | No | Sender + alert recipient for emails. |
| `GMAIL_APP_PASSWORD` | No | Gmail App Password for SMTP. |

| Constant | Location | Value |
| --- | --- | --- |
| `ACCOUNT_ID` | `streamlit_app.py`, `scheduler.py`, `scripts/run_monitoring.py` | `"17841409576371357"` |
| `MODEL` | `app/ai/*` | `"claude-sonnet-4-6"` |
| `ENGAGEMENT_DROP_THRESHOLD` | `monitoring.py` | `20.0` (%) |
| `ENGAGEMENT_SPIKE_THRESHOLD` | `monitoring.py` | `30.0` (%) |
| Monitoring interval | `scheduler.py` | every 24 hours |

---

*Generated technical documentation for the InstaSight project.*
