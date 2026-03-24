import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Mission Control | CareerOS",
};

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
}

function StatCard({ label, value, sub, accent = "text-indigo-400" }: StatCardProps) {
  return (
    <div className="glass p-5">
      <div className="text-xs uppercase tracking-widest text-gray-500 mb-1">{label}</div>
      <div className={`text-3xl font-bold ${accent}`}>{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}

interface JobCardProps {
  title: string;
  company: string;
  score: number;
  decision: "APPLY_NOW" | "CONSIDER" | "SKIP";
  confidence: number;
}

function JobCard({ title, company, score, decision, confidence }: JobCardProps) {
  const decisionStyles = {
    APPLY_NOW: "bg-green-500/20 text-green-400 border-green-500/30",
    CONSIDER:  "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    SKIP:      "bg-gray-500/20 text-gray-400 border-gray-500/30",
  };
  const scoreColor = score >= 80 ? "text-green-400" : score >= 60 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="glass p-5 hover:border-indigo-500/30 transition-all group">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-white truncate group-hover:text-indigo-300 transition-colors">{title}</div>
          <div className="text-sm text-gray-400 mt-0.5">{company}</div>
        </div>
        <span className={`shrink-0 text-xs font-medium px-2.5 py-1 rounded-full border ${decisionStyles[decision]}`}>
          {decision.replace("_", " ")}
        </span>
      </div>
      <div className="flex items-center gap-4 mt-4">
        <div className="flex-1">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Match Score</span>
            <span className={scoreColor}>{score}%</span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${score >= 80 ? "bg-green-500" : score >= 60 ? "bg-yellow-500" : "bg-red-500"}`}
              style={{ width: `${score}%` }}
            />
          </div>
        </div>
        <div className="text-xs text-gray-500">
          <span className="text-gray-400">{confidence}%</span> conf
        </div>
      </div>
    </div>
  );
}

// Mock data — replace with fetch from Axum API
const MOCK_JOBS: JobCardProps[] = [
  { title: "Senior Backend Engineer", company: "GoPay", score: 91, decision: "APPLY_NOW", confidence: 88 },
  { title: "ML Engineer", company: "Tokopedia", score: 78, decision: "CONSIDER", confidence: 71 },
  { title: "Full-Stack Developer", company: "Traveloka", score: 65, decision: "CONSIDER", confidence: 60 },
  { title: "iOS Developer", company: "Grab", score: 22, decision: "SKIP", confidence: 90 },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold gradient-text">Mission Control</h1>
        <p className="text-gray-400 text-sm mt-1">Your personalized career intelligence dashboard.</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Jobs Tracked" value="142" sub="↑ 12 this week" />
        <StatCard label="Avg Match Score" value="74%" accent="text-green-400" sub="Above avg for your skills" />
        <StatCard label="Apply-Now Signals" value="5" accent="text-indigo-400" sub="Ready to apply" />
        <StatCard label="Market Index" value="🔥 1.2x" accent="text-orange-400" sub="AI roles surging" />
      </div>

      {/* Notification Banner */}
      <div className="glass border-l-4 border-indigo-500 p-4 flex items-center gap-3">
        <span className="text-indigo-400 text-lg">🔔</span>
        <div>
          <div className="text-sm font-medium text-white">Scout Agent Update</div>
          <div className="text-xs text-gray-400">3 new high-confidence jobs found. Interview prep available for 2 roles.</div>
        </div>
      </div>

      {/* Job Feed */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-500 mb-4">Top Job Matches</h2>
        <div className="grid gap-3">
          {MOCK_JOBS.map((job) => (
            <JobCard key={`${job.title}-${job.company}`} {...job} />
          ))}
        </div>
      </div>
    </div>
  );
}
