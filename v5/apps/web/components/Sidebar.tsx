"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", icon: "🏠", label: "Mission Control" },
  { href: "/jobs",      icon: "🎯", label: "Job Radar" },
  { href: "/profile",   icon: "👤", label: "My Profile" },
  { href: "/report",    icon: "📋", label: "Mission Report" },
  { href: "/coach",     icon: "🎤", label: "Interview Coach" },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="fixed top-0 left-0 h-full w-64 bg-gray-900 border-r border-gray-800 flex flex-col z-40">
      {/* Logo */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-lg font-bold">C</div>
          <div>
            <div className="font-bold text-white tracking-tight">CareerOS</div>
            <div className="text-xs text-indigo-400">v5.0 — Oxide Stack</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1">
        {NAV.map(({ href, icon, label }) => {
          const active = path.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                active
                  ? "bg-indigo-600/20 text-indigo-400 border border-indigo-600/30 font-medium"
                  : "text-gray-400 hover:text-gray-100 hover:bg-gray-800"
              }`}
            >
              <span className="text-base">{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-600 text-center">
          Powered by Axum + Next.js
        </div>
      </div>
    </aside>
  );
}
