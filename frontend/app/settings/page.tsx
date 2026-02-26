import { DashboardLayout } from "@/components/dashboard-layout";
import { SettingsPage } from "@/components/settings-page";

export default function SettingsRoute() {
  return (
    <DashboardLayout>
      <SettingsPage />
    </DashboardLayout>
  );
}
