"use client";

import { useState } from "react";

interface CoachSession {
  job_title: string;
  company: string;
  gaps_targeted: string[];
  opening_statement: string;
  coaching_plan: {
    skill: string;
    questions: string[];
    preparation_tip: string;
  }[];
}

const FALLBACK_JOBS = [
  { id: 1, label: "Senior Backend Engineer @ GoPay" },
  { id: 2, label: "ML Engineer @ Tokopedia" },
  { id: 3, label: "Full-Stack Developer @ Traveloka" },
];

function QuestionCard({
  plan,
  index,
}: {
  plan: CoachSession["coaching_plan"][0];
  index: number;
}) {
  const [answered, setAnswered] = useState(false);

  return (
    <div className={`glass p-5 space-y-3 transition-all ${answered ? "opacity-60" : ""}`}>
      <div className="flex items-center gap-3">
        <span className="w-6 h-6 rounded-full bg-indigo-600/30 border border-indigo-500/30 flex items-center justify-center text-xs font-bold text-indigo-300">
          {index + 1}
        </span>
        <span className="text-xs uppercase tracking-widest text-indigo-400 font-semibold">
          {plan.skill.toUpperCase()}
        </span>
      </div>

      <div className="space-y-2">
        {plan.questions.map((q, i) => (
          <div key={i} className="flex gap-2 text-sm text-gray-200">
            <span className="text-indigo-400 shrink-0">Q{i + 1}.</span>
            <span>{q}</span>
          </div>
        ))}
      </div>

      <div className="bg-indigo-900/20 border border-indigo-500/20 rounded-lg p-3 text-xs text-indigo-300">
        💡 {plan.preparation_tip}
      </div>

      <button
        onClick={() => setAnswered(!answered)}
        className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
          answered
            ? "bg-green-500/20 border-green-500/30 text-green-400"
            : "border-gray-700 text-gray-400 hover:border-indigo-500/50 hover:text-indigo-300"
        }`}
      >
        {answered ? "✅ Practised" : "Mark as Practised"}
      </button>
    </div>
  );
}

export default function CoachPage() {
  const [jobId, setJobId] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<CoachSession | null>(null);

  const handleCoach = async () => {
    setLoading(true);
    setSession(null);
    try {
      const res = await fetch(
        `http://localhost:8000/coach?job_id=${jobId}`,
      );
      if (res.ok) {
        const data = await res.json() as CoachSession;
        setSession(data);
      } else {
        // Fallback mock to demonstrate UI
        setSession({
          job_title: FALLBACK_JOBS.find(j => j.id === jobId)?.label.split(" @")[0] ?? "Unknown",
          company: FALLBACK_JOBS.find(j => j.id === jobId)?.label.split("@ ")[1] ?? "Unknown",
          gaps_targeted: ["docker", "kubernetes"],
          opening_statement:
            "Focus on demonstrating transferable skills and your learning velocity.",
          coaching_plan: [
            {
              skill: "docker",
              questions: [
                "What's the difference between an image and a container in Docker?",
                "Tell me about a time you had to learn docker quickly under pressure.",
              ],
              preparation_tip:
                "Review the fundamentals of docker on official docs or a 2-hour YouTube tutorial before the interview.",
            },
            {
              skill: "kubernetes",
              questions: [
                "How does a Kubernetes Deployment differ from a StatefulSet?",
                "Describe how you would handle a pod that keeps crashing (CrashLoopBackOff).",
              ],
              preparation_tip:
                "Review the fundamentals of kubernetes on official docs or a 2-hour YouTube tutorial before the interview.",
            },
          ],
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const progress =
    session ? Math.round((session.coaching_plan.length / Math.max(session.coaching_plan.length, 1)) * 100) : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Interview Coach</h1>
        <p className="text-gray-400 text-sm mt-1">
          AI-generated gap-based practice questions for your target job.
        </p>
      </div>

      {/* Job Selector */}
      <div className="glass p-5 flex flex-wrap gap-3 items-end">
        <div className="flex-1 min-w-[200px]">
          <label className="text-xs text-gray-500 uppercase tracking-widest block mb-1">
            Select Job
          </label>
          <select
            value={jobId}
            onChange={(e) => setJobId(Number(e.target.value))}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
          >
            {FALLBACK_JOBS.map((j) => (
              <option key={j.id} value={j.id}>
                {j.label}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={handleCoach}
          disabled={loading}
          className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          {loading ? "⟳ Generating…" : "🎤 Start Coaching"}
        </button>
      </div>

      {/* Session Results */}
      {session && (
        <div className="space-y-5">
          {/* Header */}
          <div className="glass p-5 border-l-4 border-indigo-500">
            <div className="font-semibold text-white">
              {session.job_title}{" "}
              <span className="text-gray-400 font-normal">@ {session.company}</span>
            </div>
            <p className="text-sm text-gray-300 mt-2">{session.opening_statement}</p>
            <div className="flex gap-2 mt-3 flex-wrap">
              {session.gaps_targeted.map((g) => (
                <span
                  key={g}
                  className="text-xs bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-full"
                >
                  gap: {g}
                </span>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div className="flex gap-4 text-sm">
            <div className="glass px-4 py-2.5 flex items-center gap-2">
              <span className="text-indigo-400 font-bold">{session.coaching_plan.length}</span>
              <span className="text-gray-400">skill gaps to practice</span>
            </div>
            <div className="glass px-4 py-2.5 flex items-center gap-2">
              <span className="text-indigo-400 font-bold">
                {session.coaching_plan.reduce((n, p) => n + p.questions.length, 0)}
              </span>
              <span className="text-gray-400">questions total</span>
            </div>
          </div>

          {/* Question Cards */}
          <div className="grid gap-4">
            {session.coaching_plan.map((plan, i) => (
              <QuestionCard key={plan.skill} plan={plan} index={i} />
            ))}
          </div>
        </div>
      )}

      {!session && !loading && (
        <div className="glass p-12 text-center text-gray-500">
          <div className="text-4xl mb-3">🎤</div>
          <div className="font-medium text-gray-300">Ready to coach</div>
          <div className="text-sm mt-1">
            Select a job and click Start Coaching to get personalized interview questions.
          </div>
        </div>
      )}
    </div>
  );
}
