import type { Metadata } from "next";

export const metadata: Metadata = { title: "My Profile | CareerOS" };

function SkillChip({ skill }: { skill: string }) {
  return (
    <span className="text-xs bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 px-2.5 py-1 rounded-full">
      {skill}
    </span>
  );
}

async function getProfile() {
  try {
    const res = await fetch("http://localhost:8000/profiles/active", { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function getAllProfiles() {
  try {
    const res = await fetch("http://localhost:8000/profiles", { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.profiles ?? [];
  } catch {
    return [];
  }
}

export default async function ProfilePage() {
  const [profile, profiles] = await Promise.all([getProfile(), getAllProfiles()]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold gradient-text">My Profile</h1>
        <p className="text-gray-400 text-sm mt-1">Manage your career profiles and resume data.</p>
      </div>

      {/* Active Profile Card */}
      {profile ? (
        <div className="glass p-6 space-y-5">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-indigo-600/30 border border-indigo-500/30 flex items-center justify-center text-2xl font-bold text-indigo-300">
              {(profile.name as string)?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div>
              <div className="text-xl font-bold text-white">{profile.name}</div>
              <div className="text-sm text-gray-400">{profile.experience_years} years experience · {profile.location_pref}</div>
              <div className="text-xs text-green-400 mt-0.5">● Active Profile</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="bg-gray-900/60 rounded-lg p-3">
              <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Min Salary</div>
              <div className="font-semibold text-white">
                Rp {((profile.salary_min as number) / 1_000_000).toFixed(0)}jt/mo
              </div>
            </div>
            <div className="bg-gray-900/60 rounded-lg p-3">
              <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Career Goal</div>
              <div className="font-semibold text-white truncate">{profile.career_goals ?? "—"}</div>
            </div>
          </div>

          {/* Skills */}
          <div>
            <div className="text-xs uppercase tracking-widest text-gray-500 mb-3">Skills ({(profile.skills as string[]).length})</div>
            <div className="flex flex-wrap gap-2">
              {(profile.skills as string[]).map(s => <SkillChip key={s} skill={s} />)}
            </div>
          </div>
        </div>
      ) : (
        <div className="glass p-12 text-center text-gray-500">
          <div className="text-4xl mb-3">👤</div>
          <div className="font-medium text-gray-300">No profile found</div>
          <div className="text-sm mt-1">Upload your CV via the API or Streamlit dashboard to get started.</div>
        </div>
      )}

      {/* All Profiles */}
      {profiles.length > 1 && (
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-500 mb-3">All Profiles ({profiles.length})</h2>
          <div className="grid gap-3">
            {(profiles as Array<{ id: number; name: string; experience_years: number; is_active: boolean; skills: string[] }>)
              .map(p => (
              <div key={p.id} className={`glass p-4 flex items-center gap-4 ${p.is_active ? "border-indigo-500/30" : ""}`}>
                <div className="w-9 h-9 rounded-lg bg-gray-800 flex items-center justify-center text-sm font-bold text-gray-400">
                  {p.name[0]?.toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-white">{p.name}</div>
                  <div className="text-xs text-gray-500">{p.experience_years}yr · {p.skills.length} skills</div>
                </div>
                {p.is_active && (
                  <span className="text-xs text-green-400 border border-green-500/30 px-2 py-0.5 rounded-full">Active</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
