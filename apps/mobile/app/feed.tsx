import { router } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { FlatList, StyleSheet, Text, View } from "react-native";

import { getToken } from "@/lib/auth";

const API_BASE =
  process.env.EXPO_PUBLIC_TIKKO_API_BASE_URL ?? "http://localhost:8000";

const WS_BASE = API_BASE.replace(/^http/i, "ws");

interface AttendanceEvent {
  type: "attendance.created";
  device_id: string;
  device_user_id: string;
  punched_at: string;
  punch_type: number;
  verify_mode: number;
}

export default function Feed() {
  const [events, setEvents] = useState<AttendanceEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const token = await getToken();
      if (cancelled) return;
      if (!token) {
        router.replace("/login");
        return;
      }
      const ws = new WebSocket(`${WS_BASE}/ws/attendance?token=${token}`);
      socketRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as AttendanceEvent;
          if (payload.type === "attendance.created") {
            setEvents((prev) => [payload, ...prev].slice(0, 200));
          }
        } catch {
          // Drop malformed payloads silently.
        }
      };
    })();

    return () => {
      cancelled = true;
      socketRef.current?.close();
    };
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.heading}>Live attendance</Text>
        <Text style={connected ? styles.dotOn : styles.dotOff}>●</Text>
      </View>

      {events.length === 0 ? (
        <Text style={styles.empty}>
          Waiting for punches. They&apos;ll appear here in real time as devices report them.
        </Text>
      ) : (
        <FlatList
          data={events}
          keyExtractor={(item, i) => `${item.device_user_id}-${item.punched_at}-${i}`}
          renderItem={({ item }) => (
            <View style={styles.row}>
              <Text style={styles.userId}>{item.device_user_id}</Text>
              <Text style={styles.time}>{item.punched_at}</Text>
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
  dotOn: { fontSize: 16, color: "#22c55e" },
  dotOff: { fontSize: 16, color: "#a3a3a3" },
  empty: { fontSize: 14, color: "#525252", marginTop: 24 },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e5e5",
  },
  userId: { fontSize: 16, fontWeight: "600" },
  time: { fontSize: 13, fontFamily: "monospace", color: "#525252" },
});
