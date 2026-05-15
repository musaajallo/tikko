import { router } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";

import {
  api,
  type AttendanceLog,
  type AttendanceSummary,
  type EmployeeMe,
  type LeaveRequest,
} from "@/lib/api";

function currentMonth(): string {
  const now = new Date();
  const yyyy = now.getUTCFullYear();
  const mm = String(now.getUTCMonth() + 1).padStart(2, "0");
  return `${yyyy}-${mm}`;
}

function formatPunchedAt(iso: string): string {
  // Show "May 14, 8:00 AM" without bringing in a date library.
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso + "T00:00:00Z").toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

const LEAVE_STATUS_COLOR: Record<LeaveRequest["status"], string> = {
  pending: "#a16207",
  approved: "#15803d",
  rejected: "#b91c1c",
};

export default function Dashboard() {
  const [employee, setEmployee] = useState<EmployeeMe | null>(null);
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [punches, setPunches] = useState<AttendanceLog[]>([]);
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await api.getMe();
        if (cancelled) return;
        if (me.employee === null) {
          // Admin/manager without enrollment — fall back to the live feed.
          router.replace("/feed");
          return;
        }
        setEmployee(me.employee);

        const [s, list, leaveList] = await Promise.all([
          api.myMonthlySummary(currentMonth()),
          api.listMyAttendance(1, 20),
          api.listMyLeaveRequests(1, 10),
        ]);
        if (cancelled) return;
        setSummary(s);
        setPunches(list.items);
        setLeaves(leaveList.items);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  if (employee === null) {
    // Awaiting the redirect to /feed.
    return <View style={styles.centered} />;
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.heading}>{employee.full_name}</Text>
        <Text style={styles.code}>#{employee.employee_code}</Text>
      </View>

      {summary !== null && (
        <View style={styles.kpiRow}>
          <View style={styles.kpiCard}>
            <Text style={styles.kpiValue}>{summary.total_punches}</Text>
            <Text style={styles.kpiLabel}>punches this month</Text>
          </View>
          <View style={styles.kpiCard}>
            <Text style={styles.kpiValue}>{summary.days_present}</Text>
            <Text style={styles.kpiLabel}>days present</Text>
          </View>
        </View>
      )}

      <Text style={styles.section}>Recent punches</Text>
      {punches.length === 0 ? (
        <Text style={styles.empty}>No punches yet this period.</Text>
      ) : (
        punches.map((item) => (
          <View key={item.id} style={styles.row}>
            <Text style={styles.userId}>{item.device_user_id}</Text>
            <Text style={styles.time}>{formatPunchedAt(item.punched_at)}</Text>
          </View>
        ))
      )}

      <Text style={styles.section}>My leave requests</Text>
      {leaves.length === 0 ? (
        <Text style={styles.empty}>No leave requests yet.</Text>
      ) : (
        leaves.map((item) => (
          <View key={item.id} style={styles.row}>
            <View style={styles.leaveLeft}>
              <Text style={styles.leaveReason}>{item.reason}</Text>
              <Text style={styles.time}>
                {formatDate(item.start_date)} – {formatDate(item.end_date)}
              </Text>
            </View>
            <Text
              style={[styles.leaveStatus, { color: LEAVE_STATUS_COLOR[item.status] }]}
            >
              {item.status}
            </Text>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 60, paddingHorizontal: 24, gap: 16 },
  centered: { flex: 1, alignItems: "center", justifyContent: "center" },
  errorText: { color: "#dc2626", fontSize: 14 },
  header: { gap: 4 },
  heading: { fontSize: 28, fontWeight: "700" },
  code: { fontSize: 14, color: "#737373", fontFamily: "monospace" },
  kpiRow: { flexDirection: "row", gap: 12 },
  kpiCard: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    backgroundColor: "#f5f5f5",
    gap: 4,
  },
  kpiValue: { fontSize: 28, fontWeight: "700" },
  kpiLabel: { fontSize: 12, color: "#525252" },
  section: { fontSize: 16, fontWeight: "600", marginTop: 8 },
  empty: { fontSize: 14, color: "#737373" },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e5e5",
  },
  userId: { fontSize: 16, fontWeight: "600" },
  time: { fontSize: 13, color: "#525252" },
  leaveLeft: { flex: 1, gap: 2 },
  leaveReason: { fontSize: 14, fontWeight: "600" },
  leaveStatus: {
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase",
  },
});
