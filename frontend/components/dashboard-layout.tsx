"use client";

import { Sidebar } from "./sidebar";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      {/* Main content - offset by sidebar width on desktop */}
      <main className="pt-16 lg:pt-0 lg:pl-[260px] transition-all duration-200">
        <div className="min-h-screen p-4 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
