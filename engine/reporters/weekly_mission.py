import os
import json
from datetime import datetime
from storage import db
from engine.rl.custom_rl import engine as rl_engine

class WeeklyMissionReporter:
    """
    Summarizes the current career execution mission.
    Outputs a consolidated plan for the upcoming week.
    """
    def generate_report(self) -> str:
        profile = db.get_profile()
        if not profile: return "No profile found."

        all_jobs = db.get_all_jobs()
        analyses = db.get_analyses()
        
        # 1. Top EV Targets
        top_targets = sorted(analyses.values(), key=lambda x: x.get("ev", 0), reverse=True)[:5]
        
        # 2. Skill Improvement Roadmap (aggregated)
        skill_gaps = {}
        for a in analyses.values():
            for gap in a.get("gaps", []):
                skill_gaps[gap] = skill_gaps.get(gap, 0) + 1
        
        top_gaps = sorted(skill_gaps.items(), key=lambda x: x[1], reverse=True)[:3]

        # 3. Market Sentiment
        from engine.scoring.pulse import calculate_real_pulse
        pulse = calculate_real_pulse()

        report = [
            f"# [+] CareerOS Weekly Mission: {datetime.now().strftime('%B %d, %Y')}",
            f"\n> *Targeting {len(profile.get('target_roles', []))} roles with an average market hiring index of {pulse['global_hiring_index']*100:.0f}%.*",
            "\n## [*] Top 3 High-EV Targets (Execution Priority)",
        ]

        for i, t in enumerate(top_targets[:3]):
            job = db.get_job(t["job_id"])
            if not job: continue
            report.append(f"{i+1}. **{job['title']}** at {job['company']}")
            report.append(f"   - **Expected Value**: `{t['ev']:.1f}`")
            report.append(f"   - **P(Interview)**: `{t.get('p_interview',0)*100:.1f}%`")
            report.append(f"   - **Strategy**: {t.get('strategy', 'Standard Match')}")
            report.append(f"   - **Warm Path**: {'YES' if job.get('is_warm_path') else 'NO'}")

        report.append("\n## [^] Skills & Training Requirements")
        if not top_gaps:
            report.append("System suggests profile is highly optimized for current market.")
        else:
            report.append("You have significant gaps in the following areas across multiple high-EV roles:")
            for skill, count in top_gaps:
                 report.append(f"- **{skill}**: Found in {count} target roles this week.")

        report.append("\n## [!] Market Intelligence Alerts")
        report.append(f"- **AI Sector Surge**: {pulse['ai_surge']}x boost detected.")
        if pulse.get("layoff_density", 0) > 0.1:
            report.append("[!] **High Volatility Alert**: Layoff signals detected in tech news feeds.")
        else:
            report.append("[OK] **Macro Stability**: No significant layoff spikes detected.")

        report.append("\n## [*] Action Items")
        report.append("1. **Outreach**: Use Aura agent to message the Top 3 targets listed above.")
        report.append(f"2. **Learning**: Dedicate time to {top_gaps[0][0] if top_gaps else 'portfolio refinement'}.")
        report.append("3. **Scouting**: Autonomous scout will run again in 4 hours.")

        report_path = "data/weekly_mission.md"
        os.makedirs("data", exist_ok=True)
        with open(report_path, "w") as f:
            f.write("\n".join(report))
        
        return report_path

if __name__ == "__main__":
    reporter = WeeklyMissionReporter()
    path = reporter.generate_report()
    print(f"Report generated at {path}")
