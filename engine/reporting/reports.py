"""
reports.py — Automated Daily/Weekly Reporting Engine
Aggregates CareerOS data into a human-readable markdown summary.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from storage import db
from engine.scoring.prep_advisor import get_market_pulse


def _get_funnel_stats() -> Dict:
    stats = db.get_pipeline_stats()
    scouted = stats.get("new", 0) + stats.get("new", 0)
    applied = stats.get("applied", 0)
    interview = stats.get("interview", 0)
    offer = stats.get("offer", 0)
    total = sum(stats.values()) or 1

    apply_rate = round((applied / total) * 100, 1)
    interview_rate = round((interview / (applied or 1)) * 100, 1)
    return {
        "raw": stats,
        "total": total,
        "scouted": stats.get("new", 0),
        "applied": applied,
        "interview": interview,
        "offer": offer,
        "apply_rate": apply_rate,
        "interview_rate": interview_rate,
    }


def _get_top_action_jobs(limit: int = 3) -> List[Dict]:
    """Returns the highest-priority unreviewed jobs with analyses."""
    analyses = db.get_analyses()
    jobs = db.get_all_jobs(status_filter="new", limit=20)

    ranked = []
    for job in jobs:
        jid = job.get("id")
        ev = analyses.get(jid, {}).get("ev", 0)
        ranked.append({
            "id": jid,
            "title": job.get("title", "Unknown"),
            "company": job.get("company", ""),
            "ev": ev,
        })

    return sorted(ranked, key=lambda x: x["ev"], reverse=True)[:limit]


def generate_system_report(period: str = "Daily") -> str:
    """Generates the full markdown system report."""
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    date_str = now.strftime("%d %B %Y")

    # Collect data
    funnel = _get_funnel_stats()
    rl_stats = db.get_rl_stats()
    pulse = get_market_pulse()
    top_jobs = _get_top_action_jobs()
    profile = db.get_profile()
    profile_name = profile.get("name", "User") if profile else "User"

    # Market Pulse labels
    hiring_pct = round(pulse.get("global_hiring_index", 1.0) * 100, 1)
    ai_surge = pulse.get("ai_surge", 1.0)
    pulse_emoji = "🔥" if ai_surge > 1.2 else "📊"
    ai_surge_label = f"🔥 AI Surge ×{ai_surge:.2f}" if ai_surge > 1.2 else f"Stable ×{ai_surge:.2f}"

    # Funnel bars (ASCII-style for markdown)
    def bar(val, total, width=20):
        filled = int((val / (total or 1)) * width)
        return "█" * filled + "░" * (width - filled)

    # Build the report
    report_lines = [
        f"# 📋 CareerOS {period} Report",
        f"**Generated:** {timestamp} | **Profile:** {profile_name}",
        "",
        "---",
        "",
        "## 📊 Application Pipeline Funnel",
        "",
        f"| Stage       | Count | Rate    | Progress |",
        f"| :---------- | ----: | ------: | :------- |",
        f"| 🆕 Scouted  | {funnel['scouted']:>5} | —       | {bar(funnel['scouted'], funnel['total'])} |",
        f"| 📨 Applied  | {funnel['applied']:>5} | {funnel['apply_rate']:>5}%  | {bar(funnel['applied'], funnel['total'])} |",
        f"| 💬 Interview| {funnel['interview']:>5} | {funnel['interview_rate']:>5}%  | {bar(funnel['interview'], funnel['total'])} |",
        f"| 🏆 Offer    | {funnel['offer']:>5} | —       | {bar(funnel['offer'], funnel['total'])} |",
        "",
        "---",
        "",
        "## 🤖 Reinforcement Learning Agent Health",
        "",
        f"| Metric         | Value |",
        f"| :------------- | ----: |",
        f"| States Learned | {rl_stats.get('total_states', 0):>5} |",
        f"| Total Q-Updates| {rl_stats.get('total_visits', 0):>5} |",
        f"| Average Q-Value| {rl_stats.get('average_q', 0.0):>5.4f} |",
        "",
        "> The RL agent continuously improves its application strategy with every interaction.",
        "",
        "---",
        "",
        "## 🌐 Live Market Pulse",
        "",
        f"| Signal              | Value              |",
        f"| :------------------ | :----------------- |",
        f"| Global Hiring Index | {hiring_pct}% capacity  |",
        f"| AI/ML Role Surge    | {ai_surge_label}      |",
        f"| Market Message      | {pulse.get('message', '—').strip()} |",
        "",
        "---",
        "",
        "## 🎯 Top Action Items (Highest EV, Unreviewed)",
        "",
    ]

    if top_jobs:
        report_lines += [
            f"| # | Title | Company | EV Score |",
            f"| - | :---- | :------ | -------: |",
        ]
        for i, job in enumerate(top_jobs, 1):
            report_lines.append(
                f"| {i} | {job['title']} | {job['company']} | {job['ev']:.2f} |"
            )
    else:
        report_lines.append(
            "> ✅ No high-priority unreviewed jobs. Consider running the radar scraper to find new leads."
        )

    report_lines += [
        "",
        "---",
        "",
        "## 🗺️ Cluster Performance Heat Map (v4.0.13)",
        "",
    ]
    try:
        cluster_stats = db.get_cluster_stats_all()
        if cluster_stats:
            report_lines += [
                f"| Cluster | Applies | Interviews | Rate | Signal |",
                f"| :------ | ------: | ---------: | ---: | :----- |",
            ]
            for cs in sorted(cluster_stats, key=lambda x: x.get("success_rate", 0), reverse=True)[:8]:
                rate = cs.get("success_rate", 0)
                signal = "🔥 Hot" if rate > 0.4 else "✅ Good" if rate > 0.2 else "❄️ Cold"
                report_lines.append(
                    f"| {cs['cluster_id']:<35} | {cs.get('total_applies',0):>7} | "
                    f"{cs.get('interviews',0):>10} | {rate:.0%} | {signal} |"
                )
        else:
            report_lines.append("> No cluster data yet — apply to more jobs to populate this map.")
    except Exception:
        report_lines.append("> Cluster data unavailable.")

    report_lines += [
        "",
        "---",
        "",
        f"*Report auto-generated by CareerOS v4.0 — {date_str}*",
    ]

    return "\n".join(report_lines)


def save_report(period: str = "Daily") -> str:
    """Generate report and save it to disk. Returns the file path."""
    content = generate_system_report(period)
    
    reports_dir = os.path.join(ROOT_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"careeros_{period.lower()}_report_{ts}.md"
    filepath = os.path.join(reports_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Report saved to: reports/{filename}")
    return filepath


def run_daily_scheduler(interval_hours: int = 24):
    """Blocking scheduler — runs save_report every N hours."""
    import time
    print(f"[SCHEDULER] Auto-report every {interval_hours}h. Ctrl+C to stop.")
    while True:
        try:
            save_report("Daily")
        except Exception as e:
            print(f"[SCHEDULER] Report failed: {e}")
        time.sleep(interval_hours * 3600)
