import { DashboardLayout } from "@/components/dashboard-layout";
import { SitesPage } from "@/components/sites-page";

export default function SitesRoute() {
  return (
    <DashboardLayout>
      <SitesPage />
    </DashboardLayout>
  );
}
