import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { api, type LeaveRequest } from "@/lib/api";

function formatDate(iso: string): string {
  try {
    // ISO yyyy-mm-dd → "May 14" for compactness.
    return new Date(iso + "T00:00:00Z").toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function Approvals() {
  const [items, setItems] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { items: rows } = await api.listLeaveRequests("pending");
      setItems(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const decide = async (id: string, decision: "approved" | "rejected") => {
    setPendingId(id);
    try {
      await api.decideLeaveRequest(id, decision);
      // Re-pull the pending list so the just-decided row drops out.
      await refresh();
    } catch (err) {
      Alert.alert(
        "Could not decide",
        err instanceof Error ? err.message : String(err),
      );
    } finally {
      setPendingId(null);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.heading}>Pending approvals</Text>
        {!loading && <Text style={styles.count}>{items.length}</Text>}
      </View>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator />
        </View>
      ) : error !== null ? (
        <View style={styles.centered}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : items.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.empty}>No pending requests.</Text>
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => (
            <View style={styles.row}>
              <View style={styles.who}>
                <Text style={styles.name}>
                  {item.employee_full_name ?? "Unknown employee"}
                </Text>
                <Text style={styles.code}>#{item.employee_code ?? "?"}</Text>
              </View>
              <Text style={styles.range}>
                {formatDate(item.start_date)} – {formatDate(item.end_date)}
              </Text>
              <Text style={styles.reason}>{item.reason}</Text>
              <View style={styles.actions}>
                <TouchableOpacity
                  accessibilityRole="button"
                  onPress={() => decide(item.id, "approved")}
                  disabled={pendingId === item.id}
                  style={[
                    styles.btn,
                    styles.approveBtn,
                    pendingId === item.id && styles.btnDisabled,
                  ]}
                >
                  <Text style={styles.approveText}>Approve</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  accessibilityRole="button"
                  onPress={() => decide(item.id, "rejected")}
                  disabled={pendingId === item.id}
                  style={[
                    styles.btn,
                    styles.rejectBtn,
                    pendingId === item.id && styles.btnDisabled,
                  ]}
                >
                  <Text style={styles.rejectText}>Reject</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 60, paddingHorizontal: 24, gap: 12 },
  header: { flexDirection: "row", alignItems: "center", gap: 8 },
  heading: { fontSize: 24, fontWeight: "700" },
  count: {
    fontSize: 12,
    color: "#525252",
    backgroundColor: "#e5e5e5",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 999,
    overflow: "hidden",
  },
  centered: { flex: 1, alignItems: "center", justifyContent: "center" },
  errorText: { color: "#dc2626", fontSize: 14 },
  empty: { fontSize: 14, color: "#737373" },
  list: { paddingBottom: 24, gap: 12 },
  row: {
    backgroundColor: "#f5f5f5",
    borderRadius: 12,
    padding: 16,
    gap: 6,
  },
  who: { flexDirection: "row", alignItems: "baseline", gap: 6 },
  name: { fontSize: 16, fontWeight: "700" },
  code: { fontSize: 12, color: "#737373", fontFamily: "monospace" },
  range: { fontSize: 14, color: "#525252" },
  reason: { fontSize: 14, color: "#171717" },
  actions: { flexDirection: "row", gap: 8, marginTop: 8 },
  btn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: "center",
  },
  approveBtn: { backgroundColor: "#22c55e" },
  approveText: { color: "#fff", fontWeight: "600" },
  rejectBtn: { backgroundColor: "#fff", borderWidth: 1, borderColor: "#d4d4d4" },
  rejectText: { color: "#171717", fontWeight: "600" },
  btnDisabled: { opacity: 0.5 },
});
