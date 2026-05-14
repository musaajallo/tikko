import { ComingSoon } from "@/components/coming-soon";

export default function ReportsPage() {
  return (
    <ComingSoon
      title="Reports"
      description="Attendance summaries, late/early counters, payroll exports."
      bullets={[
        "Per-employee monthly summary (hours, late, early, OT)",
        "Department roll-ups",
        "CSV and XLSX export",
        "Saved filters",
      ]}
    />
  );
}
