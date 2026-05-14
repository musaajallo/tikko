import { ComingSoon } from "@/components/coming-soon";

export default function SettingsPage() {
  return (
    <ComingSoon
      title="Settings"
      description="Org, users, roles, and integration preferences."
      bullets={[
        "User management and role assignments",
        "Org details (name, timezone, working week)",
        "Shift rules and overtime policy",
        "Notification preferences",
      ]}
    />
  );
}
