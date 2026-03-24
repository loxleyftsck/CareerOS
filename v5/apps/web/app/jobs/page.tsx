"use client";

import { useState } from "react";
import type { JobResult } from "@/lib/api";

const DECISION_STYLES = {
  APPLY_NOW: { badge: "bg-green-500/20 text-green-400 border-green-500/30", bar: "bg-green-500" },
  CONSIDER:  { badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30", bar: "bg-yellow-500" },
  SKIP:      { badge: "bg-gray-500/20 text-gray-400 border-gray-500/30", bar: "bg-gray-600" },
};

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
    </div>
  );
}

function JobCard({ job }: { job: JobResult }) {
  const [expanded, setExpanded] = useState(false);
  const s = DECISION_STYLES[job.decision] ?? DECISION_STYLES.SKIP;
  const scoreColor = job.calibrated_score >= 80 ? "text-green-400" : job.calibrated_score >= 55 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="glass p-5 space-y-4 hover:border-indigo-500/30 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-white truncate">{job.title}</div>
          <div className="text-sm text-gray-400 mt-0.5">{job.company}</div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${s.badge}`}>
            {job.decision.replace("_", " ")}
          </span>
          <span className={`text-2xl font-bold ${scoreColor}`}>{job.calibrated_score}%</span>
        </div>
      </div>

      {/* Progress bars */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs text-gray-500">
        {Object.entries({
          "Skill Match": job.breakdown.skill_match,
          "Exp Fit": job.breakdown.exp_match,
          "Location": job.breakdown.location_match,
          "Growth": job.breakdown.growth_potential,
        }).map(([label, val]) => (
          <div key={label}>
            <div className="flex justify-between mb-1">
              <span>{label}</span>
              <span className="text-gray-400">{val.toFixed(0)}%</span>
            </div>
            <ScoreBar value={val} color={val >= 70 ? "bg-green-500" : val >= 50 ? "bg-yellow-500" : "bg-red-500"} />
          </div>
        ))}
      </div>

      {/* EV + Confidence row */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <span>EV <span className="text-indigo-400 font-semibold">{job.ev.toFixed(1)}</span></span>
        <span>•</span>
        <span>Conf <span className="text-gray-300">{job.match_confidence.toFixed(0)}%</span></span>
        <span>•</span>
        <span>P(interview) <span className="text-gray-300">{(job.p_interview * 100).toFixed(0)}%</span></span>
        <button
          onClick={() => setExpanded(!expanded)}
          className="ml-auto text-indigo-400 hover:text-indigo-300 text-xs"
        >
          {expanded ? "▲ Hide" : "▼ Details"}
        </button>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="border-t border-gray-800 pt-4 space-y-3">
          {/* Skills */}
          <div className="flex gap-6">
            {job.matched_skills.length > 0 && (
              <div>
                <div className="text-xs uppercase tracking-widest text-gray-500 mb-2">✅ Matched</div>
                <div className="flex flex-wrap gap-1.5">
                  {job.matched_skills.map(s => (
                    <span key={s} className="text-xs bg-green-500/10 text-green-400 border border-green-500/20 px-2 py-0.5 rounded-full">{s}</span>
                  ))}
                </div>
              </div>
            )}
            {job.gaps.length > 0 && (
              <div>
                <div className="text-xs uppercase tracking-widest text-gray-500 mb-2">⚠️ Gaps</div>
                <div className="flex flex-wrap gap-1.5">
                  {job.gaps.map(g => (
                    <span key={g} className="text-xs bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-full">{g}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Application Prep */}
          {job.application_prep?.length > 0 && (
            <div>
              <div className="text-xs uppercase tracking-widest text-gray-500 mb-2">🎯 Prep Plan</div>
              <div className="space-y-1.5">
                {job.application_prep.map((p, i) => {
                  const icon = p.type === "cv" ? "📄" : p.type === "gap" ? "⚠️" : "♟️";
                  return <div key={i} className="text-sm text-gray-300">{icon} {p.action}</div>;
                })}
              </div>
            </div>
          )}

          {/* Risk */}
          <div className="text-xs text-gray-500 bg-gray-900 rounded-lg p-3">
            {job.explanation.risk_assessment}
          </div>
        </div>
      )}
    </div>
  );
}

export default function JobRadarPage() {
  const [keyword, setKeyword] = useState("Python");
  const [location, setLocation] = useState("Jakarta");
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState<JobResult[]>([]);
  const [filter, setFilter] = useState<"ALL" | "APPLY_NOW" | "CONSIDER" | "SKIP">("ALL");

  const handleScan = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/scrape`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword, location, limit: 20 }),
      });
      const data = await res.json() as { results: JobResult[] };
      setJobs(data.results ?? []);
    } catch {
      // fallback — show empty state
    } finally {
      setLoading(false);
    }
  };

  const displayed = filter === "ALL" ? jobs : jobs.filter(j => j.decision === filter);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Job Radar</h1>
        <p className="text-gray-400 text-sm mt-1">Scout, score, and rank jobs against your profile.</p>
      </div>

      {/* Search Controls */}
      <div className="glass p-5 flex flex-wrap gap-3 items-end">
        <div className="flex-1 min-w-[160px]">
          <label className="text-xs text-gray-500 uppercase tracking-widest block mb-1">Skill / Role</label>
          <input
            value={keyword}
            onChange={e => setKeyword(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
            placeholder="Python, React…"
          />
        </div>
        <div className="flex-1 min-w-[140px]">
          <label className="text-xs text-gray-500 uppercase tracking-widest block mb-1">Location</label>
          <input
            value={location}
            onChange={e => setLocation(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
            placeholder="Jakarta, Remote…"
          />
        </div>
        <button
          onClick={handleScan}
          disabled={loading}
          className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          {loading ? "⟳ Scanning…" : "⚡ Scan Now"}
        </button>
      </div>

      {/* Filter Tabs */}
      {jobs.length > 0 && (
        <div className="flex gap-2">
          {(["ALL", "APPLY_NOW", "CONSIDER", "SKIP"] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                filter === f
                  ? "bg-indigo-600/30 border-indigo-500/50 text-indigo-300"
                  : "border-gray-700 text-gray-400 hover:border-gray-500"
              }`}
            >
              {f.replace("_", " ")} {f === "ALL" ? `(${jobs.length})` : `(${jobs.filter(j => j.decision === f).length})`}
            </button>
          ))}
        </div>
      )}

      {/* Results */}
      {loading && (
        <div className="flex items-center justify-center py-16 text-gray-500">
          <div className="text-center">
            <div className="text-4xl animate-pulse mb-3">🔭</div>
            <div className="text-sm">Scout agent scanning…</div>
          </div>
        </div>
      )}

      {!loading && jobs.length === 0 && (
        <div className="glass p-12 text-center text-gray-500">
          <div className="text-4xl mb-3">📡</div>
          <div className="font-medium text-gray-300">No jobs loaded yet</div>
          <div className="text-sm mt-1">Enter a skill and click Scan Now to start scouting.</div>
        </div>
      )}

      <div className="grid gap-3">
        {displayed.map(job => <JobCard key={job.job_id} job={job} />)}
      </div>
    </div>
  );
}
