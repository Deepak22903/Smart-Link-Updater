"use client";

import dynamic from "next/dynamic";
import { DashboardLayout } from "@/components/dashboard-layout";

const HomeDashboard = dynamic(
  () => import("@/components/home-dashboard").then((m) => ({ default: m.HomeDashboard })),
  { ssr: false }
);

export default function HomePage() {
  return (
    <DashboardLayout>
      <HomeDashboard />
    </DashboardLayout>
  );
}
