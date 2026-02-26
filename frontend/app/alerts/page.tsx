"use client";

import dynamic from "next/dynamic";
import { DashboardLayout } from "@/components/dashboard-layout";

const AlertsPage = dynamic(
  () =>
    import("@/components/alerts-page").then((m) => ({
      default: m.AlertsPage,
    })),
  { ssr: false }
);

export default function AlertsRoute() {
  return (
    <DashboardLayout>
      <AlertsPage />
    </DashboardLayout>
  );
}
