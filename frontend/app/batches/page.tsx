"use client";

import dynamic from "next/dynamic";
import { DashboardLayout } from "@/components/dashboard-layout";

const BatchesPage = dynamic(
  () =>
    import("@/components/batches-page").then((m) => ({
      default: m.BatchesPage,
    })),
  { ssr: false }
);

export default function BatchesRoute() {
  return (
    <DashboardLayout>
      <BatchesPage />
    </DashboardLayout>
  );
}
