"""
InstaSight — Instagram Business Analytics Dashboard

Run from project root:
    streamlit run app/dashboard/streamlit_app.py
"""

import sys
from datetime import datetime
from pathlib import Path

import anthropic
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.ai.strategy_generator import generate_strategy  # noqa: E402
from app.ai.strategy_generator import (  # noqa: E402
    SYSTEM_PROMPT as STRATEGY_PROMPT,
    MODEL as STRATEGY_MODEL,
)
# from app.ai.weekly_planner import coming_week_bounds, generate_weekly_plan
from app.ai.performance_advisor import generate_performance_advice  # noqa: E402
from app.ai.performance_advisor import (  # noqa: E402
    SYSTEM_PROMPT as ADVISOR_PROMPT,
    MODEL as ADVISOR_MODEL,
)
# from app.notifications.email_sender import send_weekly_plan_email
from app.analytics.scheduler import start_scheduler, get_scheduler_status  # noqa: E402
from app.analytics.monitoring import run_daily_monitoring, save_daily_snapshot  # noqa: E402
from app.analytics.trend_analysis import get_performance_trend, get_trend_summary  # noqa: E402
from app.analytics.metrics import (  # noqa: E402
    avg_engagement_rate,
    best_posting_day,
    content_type_performance,
    posting_frequency,
    top_performing_posts,
)
from app.analytics.analysis import analyze_account  # noqa: E402
from app.analytics.report_builder import build_report, build_prompt_context  # noqa: E402
from app.config import load_settings  # noqa: E402
from app.analytics.sync_service import sync_account_data  # noqa: E402
from app.api.meta_client import MetaClient  # noqa: E402
from app.database.connection import get_connection, init_db  # noqa: E402


ACCOUNT_ID = "17841409576371357"

# Brand palette
PRIMARY = "#405DE6"
BG = "#FFFFFF"
CARD = "#F8F9FA"
TEXT_PRIMARY = "#1A1A2E"
TEXT_SECONDARY = "#6C757D"
SUCCESS = "#28A745"
WARNING = "#FFC107"
DANGER = "#DC3545"

BENCHMARK_ENGAGEMENT_LOW = 1.0
BENCHMARK_ENGAGEMENT_HIGH = 3.0
BENCHMARK_POSTS_PER_WEEK = 3.0

PAGES = ("Overview", "Post Analysis", "Trends", "AI Strategy", "Performance Advisor")


def _inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }}

        .stApp {{
            background-color: {BG};
        }}

        [data-testid="stSidebar"] {{
            background-color: {CARD};
            border-right: 1px solid #E9ECEF;
        }}

        .page-title {{
            font-size: 1.75rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            margin: 0 0 0.25rem 0;
        }}

        .page-subtitle {{
            font-size: 0.95rem;
            color: {TEXT_SECONDARY};
            margin: 0 0 1.5rem 0;
        }}

        .kpi-card {{
            background: {CARD};
            border: 1px solid #E9ECEF;
            border-radius: 10px;
            padding: 1.25rem 1.5rem;
            min-height: 120px;
        }}

        .kpi-icon {{
            font-size: 1.25rem;
            margin-bottom: 0.35rem;
        }}

        .kpi-name {{
            font-size: 0.8rem;
            font-weight: 600;
            color: {TEXT_SECONDARY};
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            margin: 0.25rem 0;
        }}

        .kpi-context {{
            font-size: 0.85rem;
            color: {TEXT_SECONDARY};
        }}

        .kpi-context.success {{ color: {SUCCESS}; }}
        .kpi-context.warning {{ color: {WARNING}; }}
        .kpi-context.danger {{ color: {DANGER}; }}

        .info-card {{
            background: {CARD};
            border: 1px solid #E9ECEF;
            border-radius: 10px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
        }}

        .sidebar-brand {{
            font-size: 1.35rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            margin-bottom: 0.15rem;
        }}

        .sidebar-section {{
            font-size: 0.7rem;
            font-weight: 600;
            color: {TEXT_SECONDARY};
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin: 1.25rem 0 0.5rem 0;
        }}

        .account-box {{
            background: {BG};
            border: 1px solid #E9ECEF;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            font-size: 0.9rem;
            color: {TEXT_PRIMARY};
        }}

        .account-box strong {{
            color: {PRIMARY};
        }}

        .strategy-box {{
            background: {CARD};
            border: 1px solid #E9ECEF;
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _truncate(text: str | None, max_len: int) -> str:
    value = (text or "").strip().replace("\n", " ")
    if not value:
        return "(no caption)"
    if len(value) <= max_len:
        return value
    return value[:max_len] + "..."


def _parse_post_date(timestamp: str | None) -> datetime | None:
    if not timestamp:
        return None
    normalized = timestamp.strip()
    if normalized.endswith("+0000"):
        normalized = normalized[:-5] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _format_date(timestamp: str | None) -> str:
    parsed = _parse_post_date(timestamp)
    if parsed is None:
        return "—"
    return parsed.strftime("%d %b %Y")


def _plotly_light(fig: go.Figure, title: str, height: int = 420) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=TEXT_PRIMARY)),
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family="Inter, Segoe UI, sans-serif", color=TEXT_PRIMARY, size=12),
        height=height,
        margin=dict(l=24, r=24, t=56, b=64),
        xaxis=dict(
            gridcolor="#E9ECEF",
            linecolor="#DEE2E6",
            tickfont=dict(color=TEXT_SECONDARY),
            title_font=dict(color=TEXT_SECONDARY),
        ),
        yaxis=dict(
            gridcolor="#E9ECEF",
            linecolor="#DEE2E6",
            tickfont=dict(color=TEXT_SECONDARY),
            title_font=dict(color=TEXT_SECONDARY),
        ),
        hoverlabel=dict(bgcolor=BG, font_size=12, font_color=TEXT_PRIMARY),
    )
    return fig


def _kpi_card(icon: str, name: str, value: str, context: str, context_class: str = "") -> None:
    ctx_cls = f" kpi-context {context_class}".strip() if context_class else "kpi-context"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-name">{name}</div>
            <div class="kpi-value">{value}</div>
            <div class="{ctx_cls}">{context}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=60)
def _load_last_synced(account_id: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT synced_at FROM accounts WHERE id = ?",
            (account_id,),
        ).fetchone()
    return row["synced_at"] if row else None


@st.cache_data(ttl=60)
def _load_posts_table(account_id: str) -> pd.DataFrame:
    with get_connection() as conn:
        followers_row = conn.execute(
            "SELECT followers_count FROM accounts WHERE id = ?",
            (account_id,),
        ).fetchone()
        followers = int(followers_row["followers_count"] or 0) if followers_row else 0

        rows = conn.execute(
            """
            SELECT
                p.caption,
                p.media_type,
                p.timestamp,
                i.likes_count,
                i.comments_count
            FROM posts p
            INNER JOIN insights i ON i.id = (
                SELECT id FROM insights
                WHERE post_id = p.id
                ORDER BY synced_at DESC
                LIMIT 1
            )
            WHERE p.account_id = ?
            """,
            (account_id,),
        ).fetchall()

    records = []
    for row in rows:
        likes = int(row["likes_count"] or 0)
        comments = int(row["comments_count"] or 0)
        engagement = (likes + comments) / followers * 100 if followers > 0 else 0.0
        parsed = _parse_post_date(row["timestamp"])
        records.append(
            {
                "Caption": _truncate(row["caption"], 80),
                "Media Type": row["media_type"] or "UNKNOWN",
                "Posted Date": parsed.date() if parsed else None,
                "Likes": likes,
                "Comments": comments,
                "Engagement Rate": round(engagement, 2),
            }
        )

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values("Engagement Rate", ascending=False).reset_index(drop=True)
    return df


@st.cache_data(ttl=60)
def _load_posts_for_chart(account_id: str) -> pd.DataFrame:
    with get_connection() as conn:
        followers_row = conn.execute(
            "SELECT followers_count FROM accounts WHERE id = ?",
            (account_id,),
        ).fetchone()
        followers = int(followers_row["followers_count"] or 0) if followers_row else 0

        rows = conn.execute(
            """
            SELECT p.caption, p.timestamp, i.likes_count, i.comments_count
            FROM posts p
            INNER JOIN insights i ON i.id = (
                SELECT id FROM insights
                WHERE post_id = p.id
                ORDER BY synced_at DESC
                LIMIT 1
            )
            WHERE p.account_id = ?
            ORDER BY p.timestamp ASC
            """,
            (account_id,),
        ).fetchall()

    data = []
    for row in rows:
        likes = int(row["likes_count"] or 0)
        comments = int(row["comments_count"] or 0)
        engagement = (likes + comments) / followers * 100 if followers > 0 else 0.0
        parsed = _parse_post_date(row["timestamp"])
        data.append(
            {
                "post_date": parsed,
                "post_date_label": _format_date(row["timestamp"]),
                "caption": _truncate(row["caption"], 60),
                "likes": likes,
                "comments": comments,
                "engagement_rate": round(engagement, 2),
            }
        )
    return pd.DataFrame(data)


@st.cache_data(ttl=3600)
def _load_report(account_id: str) -> dict:
    init_db()
    return build_report(account_id)


@st.cache_data(ttl=3600)
def _load_analysis(account_id: str) -> dict:
    init_db()
    return analyze_account(account_id)


def _engagement_context(rate: float) -> tuple[str, str]:
    if rate < BENCHMARK_ENGAGEMENT_LOW:
        return f"Below benchmark ({BENCHMARK_ENGAGEMENT_LOW}-{BENCHMARK_ENGAGEMENT_HIGH}%)", "danger"
    if rate > BENCHMARK_ENGAGEMENT_HIGH:
        return f"Above benchmark ({BENCHMARK_ENGAGEMENT_LOW}-{BENCHMARK_ENGAGEMENT_HIGH}%)", "success"
    return f"Within benchmark ({BENCHMARK_ENGAGEMENT_LOW}-{BENCHMARK_ENGAGEMENT_HIGH}%)", "success"


def _frequency_context(posts_per_week: float) -> tuple[str, str]:
    if posts_per_week < BENCHMARK_POSTS_PER_WEEK:
        return f"⚠ Below target (min. {BENCHMARK_POSTS_PER_WEEK:.0f}/week)", "danger"
    return f"On track (min. {BENCHMARK_POSTS_PER_WEEK:.0f}/week)", "success"


def _render_sidebar(
    username: str,
    followers: int,
    last_synced: str | None,
) -> str:
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">📊 InstaSight</div>', unsafe_allow_html=True)
        st.caption("Dental clinic analytics")

        st.markdown('<div class="sidebar-section">Account</div>', unsafe_allow_html=True)
        synced_label = last_synced or "Not synced yet"
        st.markdown(
            f"""
            <div class="account-box">
                <div><strong>@{username}</strong></div>
                <div style="margin-top:6px;">👥 {followers:,} followers</div>
                <div style="margin-top:6px; color:{TEXT_SECONDARY}; font-size:0.8rem;">
                    Last synced: {synced_label}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section">Actions</div>', unsafe_allow_html=True)
        if st.button("🔄 Sync Data", use_container_width=True, type="primary"):
            try:
                with st.spinner("Syncing Instagram data..."):
                    init_db()
                    result = sync_account_data(MetaClient())
                st.session_state["flash"] = (
                    f"Sync complete — {result['posts_synced']} posts, "
                    f"{result['insights_synced']} insights."
                )
                st.session_state.pop("sync_error", None)
                st.cache_data.clear()
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.session_state["sync_error"] = str(exc)
                st.session_state.pop("flash", None)
                st.error("⚠️ Sync failed — please check your access token in .env")
                with st.expander("Error details"):
                    st.code(str(exc))

        if st.button("🤖 Generate Strategy", use_container_width=True):
            st.session_state["nav_page"] = "AI Strategy"
            st.session_state["trigger_strategy"] = True
            st.rerun()

        if st.session_state.get("flash"):
            st.success(st.session_state["flash"])

        st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)
        page = st.radio(
            "Go to",
            PAGES,
            index=PAGES.index(st.session_state.get("nav_page", "Overview")),
            label_visibility="collapsed",
        )
        st.session_state["nav_page"] = page

        st.markdown('<div class="sidebar-section">Monitoring</div>',
                    unsafe_allow_html=True)
        status = get_scheduler_status()
        next_run = status.get("next_run", "unknown")
        st.caption("🟢 Auto-monitoring active")
        st.caption(f"Next check: {next_run}")

        if st.button("▶ Run Check Now", use_container_width=True):
            with st.spinner("Running monitoring check..."):
                result = run_daily_monitoring(ACCOUNT_ID)
            alerts = result.get("alerts", [])
            if alerts:
                for alert in alerts:
                    st.warning(f"⚠️ {alert['message']}")
            else:
                st.success("✅ Everything looks normal")

    return page


def _page_overview(report: dict, username: str) -> None:
    summary = report["account_summary"]
    frequency = report.get("posting_frequency_detail", {})
    avg_rate = summary["avg_engagement_rate"]
    posts_per_week = float(
        frequency.get("posts_per_week", report["patterns"]["posts_per_week"])
    )
    synced = summary.get("synced_posts_in_db", 0)

    st.markdown('<p class="page-title">Analytics Overview</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="page-subtitle">Performance data for @{username} — Dental-B</p>',
        unsafe_allow_html=True,
    )

    eng_ctx, eng_cls = _engagement_context(avg_rate)
    freq_ctx, freq_cls = _frequency_context(posts_per_week)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _kpi_card("👥", "Followers", f"{summary['followers']:,}", "Total audience")
    with c2:
        _kpi_card("📈", "Engagement Rate", f"{avg_rate}%", eng_ctx, eng_cls)
    with c3:
        _kpi_card("📸", "Posts Synced", str(synced), "In local database")
    with c4:
        _kpi_card("📅", "Posts/Week", str(posts_per_week), freq_ctx, freq_cls)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns(2)

    chart_df = _load_posts_for_chart(ACCOUNT_ID)

    with left:
        if chart_df.empty:
            st.info("No post data available.")
        else:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=chart_df["post_date"],
                    y=chart_df["engagement_rate"],
                    mode="lines+markers",
                    name="Engagement",
                    line=dict(color=PRIMARY, width=2),
                    marker=dict(size=9, color=PRIMARY),
                    customdata=chart_df[
                        ["caption", "likes", "comments", "post_date_label"]
                    ].values,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Date: %{customdata[3]}<br>"
                        "Likes: %{customdata[1]}<br>"
                        "Comments: %{customdata[2]}<br>"
                        "Engagement: %{y:.2f}%<extra></extra>"
                    ),
                )
            )
            fig.add_hline(
                y=avg_rate,
                line_dash="dash",
                line_color=TEXT_SECONDARY,
                annotation_text=f"Average {avg_rate}%",
                annotation_position="right",
                annotation_font_color=TEXT_SECONDARY,
            )
            fig = _plotly_light(fig, "Engagement Rate per Post")
            fig.update_xaxes(title="Post Date", tickformat="%d %b %Y")
            fig.update_yaxes(title="Engagement Rate (%)")
            st.plotly_chart(fig, use_container_width=True)

    with right:
        top_posts = top_performing_posts(ACCOUNT_ID, limit=5)
        if not top_posts:
            st.info("No top posts available.")
        else:
            top_df = pd.DataFrame(
                [
                    {
                        "caption": _truncate(p.get("caption"), 30),
                        "engagement_rate": p["engagement_rate"],
                    }
                    for p in top_posts
                ]
            )
            fig_top = px.bar(
                top_df,
                x="engagement_rate",
                y="caption",
                orientation="h",
                text="engagement_rate",
                color_discrete_sequence=[PRIMARY],
                labels={"engagement_rate": "Engagement (%)", "caption": "Post"},
            )
            fig_top.update_traces(
                texttemplate="%{text}%",
                textposition="outside",
                marker_line_width=0,
            )
            fig_top = _plotly_light(fig_top, "Top 5 Posts by Engagement")
            fig_top.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_top, use_container_width=True)

    st.markdown('<p class="page-title" style="font-size:1.15rem;">Post Details Table</p>', unsafe_allow_html=True)
    table_df = _load_posts_table(ACCOUNT_ID)
    if table_df.empty:
        st.info("No posts in database.")
    else:
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Caption": st.column_config.TextColumn("Caption", width="large"),
                "Media Type": st.column_config.TextColumn("Media Type", width="small"),
                "Posted Date": st.column_config.DateColumn("Posted Date", format="DD MMM YYYY"),
                "Likes": st.column_config.NumberColumn("Likes ❤️", format="%d"),
                "Comments": st.column_config.NumberColumn("Comments 💬", format="%d"),
                "Engagement Rate": st.column_config.NumberColumn(
                    "Engagement Rate 📊",
                    format="%.2f%%",
                ),
            },
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<p class="page-title" style="font-size:1.15rem;">Recent Alerts</p>',
        unsafe_allow_html=True,
    )

    with get_connection() as conn:
        alert_rows = conn.execute(
            """SELECT alert_type, message, metric_value,
                      metric_previous, sent_at
               FROM alerts
               WHERE account_id = ?
               ORDER BY sent_at DESC LIMIT 5""",
            (ACCOUNT_ID,),
        ).fetchall()

    if alert_rows:
        for row in alert_rows:
            if "drop" in row["alert_type"] or "inactivity" in row["alert_type"]:
                st.warning(f"⚠️ {row['message']} — {row['sent_at'][:10]}")
            else:
                st.success(f"📈 {row['message']} — {row['sent_at'][:10]}")
    else:
        st.caption("No alerts yet — monitoring is active.")


def _page_post_analysis(report: dict, username: str) -> None:
    st.markdown('<p class="page-title">Post Analysis</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="page-subtitle">Content and timing insights for @{username} — Dental-B</p>',
        unsafe_allow_html=True,
    )

    avg = avg_engagement_rate(ACCOUNT_ID)
    freq = posting_frequency(ACCOUNT_ID)
    best_day = best_posting_day(ACCOUNT_ID)
    content_types = content_type_performance(ACCOUNT_ID)

    m1, m2, m3 = st.columns(3)
    with m1:
        _kpi_card("📊", "Avg Engagement", f"{avg['avg_engagement_rate']}%", f"{avg['post_count']} posts analyzed")
    with m2:
        _kpi_card(
            "📅",
            "Best Day",
            best_day.get("day") or "—",
            f"{best_day.get('avg_engagement_rate', 0)}% avg engagement",
        )
    with m3:
        _kpi_card(
            "🗓️",
            "Posting Cadence",
            f"{freq['posts_per_week']}/week",
            f"Over {freq.get('weeks_span', 0)} weeks of data",
        )

    col_a, col_b = st.columns(2)

    with col_a:
        if content_types:
            ct_df = pd.DataFrame(content_types)
            fig_ct = px.bar(
                ct_df,
                x="media_type",
                y="avg_engagement_rate",
                text="post_count",
                color_discrete_sequence=[PRIMARY],
                labels={
                    "media_type": "Media Type",
                    "avg_engagement_rate": "Avg Engagement (%)",
                    "post_count": "Posts",
                },
                title="Engagement by Media Type",
            )
            fig_ct.update_traces(texttemplate="%{text} posts", textposition="outside")
            fig_ct = _plotly_light(fig_ct, "Engagement by Media Type")
            st.plotly_chart(fig_ct, use_container_width=True)
        else:
            st.info("No media type data.")

    with col_b:
        insights = report.get("growth_insights", [])
        st.markdown(
            '<div class="info-card"><strong>Key patterns from your data</strong></div>',
            unsafe_allow_html=True,
        )
        if insights:
            for line in insights:
                st.markdown(f"- {line}")
        else:
            st.caption("Run sync to populate insights.")


def _stream_strategy() -> None:
    report = build_report(ACCOUNT_ID)
    context = build_prompt_context(report)

    client = anthropic.Anthropic(api_key=load_settings().anthropic_api_key)
    strategy_placeholder = st.empty()
    full_text = ""
    with client.messages.stream(
        model=STRATEGY_MODEL,
        max_tokens=4096,
        system=STRATEGY_PROMPT,
        messages=[{"role": "user", "content": context}],
    ) as stream:
        for text in stream.text_stream:
            full_text += text
            strategy_placeholder.markdown(full_text + "▌")

    strategy_placeholder.markdown(full_text)
    st.session_state["strategy"] = full_text
    st.session_state["strategy_generated_at"] = datetime.now().isoformat()
    st.session_state["strategy_copied"] = False


def _page_ai_strategy(report: dict, username: str) -> None:
    st.markdown('<p class="page-title">AI Growth Strategy</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">One-time comprehensive analysis and '
        'growth roadmap for your account</p>',
        unsafe_allow_html=True,
    )

    summary = report["account_summary"]
    frequency = report.get("posting_frequency_detail", {})
    posts_per_week = frequency.get("posts_per_week", report["patterns"]["posts_per_week"])

    st.markdown(
        f"""
        <div class="info-card">
            <strong>Account snapshot</strong><br>
            Followers: <strong>{summary['followers']:,}</strong> &nbsp;|&nbsp;
            Engagement: <strong>{summary['avg_engagement_rate']}%</strong> &nbsp;|&nbsp;
            Posts/week: <strong>{posts_per_week}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("trigger_strategy"):
        st.session_state["trigger_strategy"] = False
        try:
            _stream_strategy()
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Strategy generation failed: {exc}")

    if not st.session_state.get("strategy"):
        if st.button("Generate Strategy", type="primary", use_container_width=False):
            try:
                _stream_strategy()
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Strategy generation failed: {exc}")
    else:
        generated_at = st.session_state.get("strategy_generated_at", "")
        st.caption(f"Generated: {generated_at}")
        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
        st.markdown(st.session_state["strategy"])
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("📋 Copy Strategy", use_container_width=False):
            st.session_state["strategy_copied"] = True
        if st.session_state.get("strategy_copied"):
            st.success("Copied!")


# def _generate_weekly_plan_with_progress() -> dict:
#     progress = st.progress(0, text="Loading account data...")
#     _load_report(ACCOUNT_ID)
#     progress.progress(33, text="Analyzing performance patterns...")
#     _load_analysis(ACCOUNT_ID)
#     progress.progress(66, text="Generating weekly plan with AI...")
#     result = generate_weekly_plan(ACCOUNT_ID)
#     progress.progress(100, text="Done!")
#     progress.empty()
#     return result


# def _page_weekly_plan(report: dict, username: str) -> None:
#     st.markdown('<p class="page-title">Weekly Plan</p>', unsafe_allow_html=True)
#     st.markdown(
#         '<p class="page-subtitle">Concrete weekly action plan with '
#         'ready-to-use captions and hashtags. New plan each week.</p>',
#         unsafe_allow_html=True,
#     )
#
#     week_start, week_end = coming_week_bounds()
#     st.markdown(
#         f"""
#         <div class="info-card">
#             <strong>Upcoming Week</strong><br>
#             {week_start.strftime("%d %b %Y")} (Monday) &nbsp;→&nbsp;
#             {week_end.strftime("%d %b %Y")} (Sunday)
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )
#
#     if not st.session_state.get("weekly_plan"):
#         if st.button("🗓️ Generate Weekly Plan", type="primary"):
#             try:
#                 result = _generate_weekly_plan_with_progress()
#                 st.session_state["weekly_plan"] = result["plan"]
#                 st.session_state["weekly_plan_result"] = result
#                 st.session_state["weekly_plan_generated_at"] = result["generated_at"]
#                 st.session_state["weekly_plan_week"] = (
#                     f"{result['week_start']} → {result['week_end']}"
#                 )
#                 st.rerun()
#             except Exception as exc:  # noqa: BLE001
#                 st.error(f"Plan generation failed: {exc}")
#     else:
#         generated_at = st.session_state.get("weekly_plan_generated_at", "")
#         week_label = st.session_state.get("weekly_plan_week", "")
#         st.caption(f"Generated: {generated_at} · Week: {week_label}")
#         st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
#         st.markdown(st.session_state["weekly_plan"])
#         st.markdown("</div>", unsafe_allow_html=True)
#
#         if st.button("🗓️ Regenerate Plan", use_container_width=False):
#             st.session_state.pop("weekly_plan", None)
#             st.session_state.pop("weekly_plan_result", None)
#             st.rerun()
#
#         st.markdown("---")
#         st.markdown("**📧 Send this plan via email**")
#         recipient_email = st.text_input(
#             "Recipient email address",
#             key="weekly_plan_recipient",
#             placeholder="name@example.com",
#         )
#         if st.button("📧 Send Weekly Plan via Email", type="primary"):
#             if not recipient_email or "@" not in recipient_email:
#                 st.warning("Please enter a valid email address.")
#             else:
#                 with st.spinner("Sending email..."):
#                     sent = send_weekly_plan_email(
#                         ACCOUNT_ID,
#                         recipient_email,
#                         plan=st.session_state.get("weekly_plan_result"),
#                     )
#                 if sent:
#                     st.success(f"✅ Weekly plan sent to {recipient_email}!")
#                 else:
#                     st.error("❌ Failed to send email. Check your Gmail settings.")


def _page_performance_advisor(report: dict, username: str) -> None:
    st.markdown('<p class="page-title">Performance Advisor</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="page-subtitle">Data-driven diagnosis and concrete recommendations for @{username}</p>',
        unsafe_allow_html=True,
    )

    summary = report["account_summary"]
    frequency = report.get("posting_frequency_detail", {})
    posts_per_week = frequency.get("posts_per_week", report["patterns"]["posts_per_week"])
    best_day_data = report.get("best_posting_day", {})
    patterns = report.get("patterns", {})

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _kpi_card("📈", "Avg Engagement", f"{summary['avg_engagement_rate']}%",
                  "Average across all posts")
    with c2:
        _kpi_card("📅", "Posts/Week", str(posts_per_week),
                  "Current frequency")
    with c3:
        _kpi_card("🏆", "Best Day", best_day_data.get("day") or "—",
                  f"{best_day_data.get('avg_engagement_rate', 0)}% avg engagement")
    with c4:
        _kpi_card("🎬", "Best Format", patterns.get("best_content_type") or "—",
                  "Based on avg engagement")

    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.get("performance_advice"):
        if st.button("🔍 Analyze Performance", type="primary"):
            try:
                report = build_report(ACCOUNT_ID)
                context = build_prompt_context(report)
                # append diagnosis request
                summary = report["account_summary"]
                frequency = report.get("posting_frequency_detail", {})
                context += f"""

=== DIAGNOSIS REQUEST ===
Do NOT suggest captions or weekly plans.
Diagnose: Is {summary['avg_engagement_rate']}% engagement good or bad for this account size?
Is {frequency.get('posts_per_week', 0)} posts/week optimal?
What does the gap between total_posts={summary['total_posts']} and synced_posts={summary['synced_posts_in_db']} tell us?
Which content type should they double down on based on the breakdown data?
"""

                client = anthropic.Anthropic(api_key=load_settings().anthropic_api_key)
                advice_placeholder = st.empty()
                full_text = ""
                with client.messages.stream(
                    model=ADVISOR_MODEL,
                    max_tokens=2048,
                    system=ADVISOR_PROMPT,
                    messages=[{"role": "user", "content": context}],
                ) as stream:
                    for text in stream.text_stream:
                        full_text += text
                        advice_placeholder.markdown(full_text + "▌")

                advice_placeholder.markdown(full_text)
                st.session_state["performance_advice"] = full_text
                st.session_state["performance_advice_at"] = datetime.now().isoformat()
                st.rerun()
            except Exception as exc:
                st.error(f"Generation failed: {exc}")
    else:
        generated_at = st.session_state.get("performance_advice_at", "")
        st.caption(f"Generated: {generated_at}")
        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
        st.markdown(st.session_state["performance_advice"])
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("🔄 Re-analyze", use_container_width=False):
            st.session_state.pop("performance_advice", None)
            st.session_state.pop("performance_advice_at", None)
            st.rerun()


def _page_trends(username: str) -> None:
    st.markdown('<p class="page-title">Performance Trends</p>',
                unsafe_allow_html=True)
    st.markdown(
        f'<p class="page-subtitle">Historical performance tracking for @{username}</p>',
        unsafe_allow_html=True,
    )

    days_option = st.radio(
        "Time period",
        [7, 30, 90],
        format_func=lambda x: f"Last {x} days",
        horizontal=True,
        index=1,
    )

    trend_data = get_performance_trend(ACCOUNT_ID, days=days_option)
    summary = get_trend_summary(ACCOUNT_ID, days=days_option)

    if not summary.get("has_data"):
        st.info(summary.get(
            "message",
            "Not enough data yet. Run monitoring daily to build trend history.",
        ))
        st.markdown("### How to build trend data")
        st.markdown(
            "Click **▶ Run Check Now** in the sidebar daily. "
            "After 2+ days of data, trends will appear here."
        )
        return

    # Summary KPI row
    direction_icon = "📈" if summary["trend_direction"] == "up" else \
                     "📉" if summary["trend_direction"] == "down" else "➡️"
    change_class = "success" if summary["engagement_change"] >= 0 else "danger"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _kpi_card(
            direction_icon,
            "Engagement Trend",
            f"{summary['engagement_end']}%",
            f"{'+' if summary['engagement_change'] >= 0 else ''}"
            f"{summary['engagement_change']}% vs {summary['days_tracked']} days ago",
            change_class,
        )
    with c2:
        _kpi_card(
            "👥",
            "Followers Change",
            f"{'+' if summary['followers_change'] >= 0 else ''}"
            f"{summary['followers_change']}",
            f"{summary['followers_start']} → {summary['followers_end']}",
        )
    with c3:
        _kpi_card(
            "📅",
            "Avg Posts/Week",
            str(summary["avg_posts_per_week"]),
            f"Over {summary['snapshots_count']} days tracked",
        )
    with c4:
        _kpi_card(
            "📊",
            "Data Points",
            str(summary["snapshots_count"]),
            f"{summary['first_date']} → {summary['last_date']}",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if trend_data:
        df = pd.DataFrame(trend_data)

        # Engagement trend chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["snapshot_date"],
            y=df["avg_engagement_rate"],
            mode="lines+markers",
            name="Engagement Rate",
            line=dict(color="#405DE6", width=2),
            marker=dict(size=8, color="#405DE6"),
            hovertemplate=(
                "Date: %{x}<br>"
                "Engagement: %{y:.2f}%<extra></extra>"
            ),
        ))
        fig = _plotly_light(fig, "Engagement Rate Trend")
        fig.update_xaxes(title="Date")
        fig.update_yaxes(title="Engagement Rate (%)")
        st.plotly_chart(fig, use_container_width=True)

        # Posts per week trend chart
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df["snapshot_date"],
            y=df["posts_this_week"],
            name="Posts This Week",
            marker_color="#405DE6",
            hovertemplate=(
                "Date: %{x}<br>"
                "Posts: %{y}<extra></extra>"
            ),
        ))
        fig2 = _plotly_light(fig2, "Posts Per Week Over Time")
        fig2.update_xaxes(title="Date")
        fig2.update_yaxes(title="Posts Count")
        st.plotly_chart(fig2, use_container_width=True)


def main() -> None:
    st.set_page_config(
        page_title="InstaSight Analytics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_styles()

    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "Overview"

    if "scheduler_started" not in st.session_state:
        start_scheduler()
        st.session_state["scheduler_started"] = True

    try:
        report = _load_report(ACCOUNT_ID)
        username = report["account_summary"]["username"]
        followers = report["account_summary"]["followers"]
    except Exception as exc:  # noqa: BLE001
        st.error(f"Unable to load data: {exc}")
        st.info("Use **Sync Data** in the sidebar to fetch Instagram metrics.")
        _render_sidebar("dentalb_ku", 0, None)
        return

    last_synced = _load_last_synced(ACCOUNT_ID)
    page = _render_sidebar(username, followers, last_synced)

    if page == "Overview":
        _page_overview(report, username)
    elif page == "Post Analysis":
        _page_post_analysis(report, username)
    elif page == "Trends":
        _page_trends(username)
    elif page == "AI Strategy":
        _page_ai_strategy(report, username)
    elif page == "Performance Advisor":
        _page_performance_advisor(report, username)


if __name__ == "__main__":
    main()
