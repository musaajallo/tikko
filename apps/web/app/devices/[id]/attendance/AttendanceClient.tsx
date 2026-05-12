"use client";

import { useCallback, useEffect, useState } from "react";

import { api, type AttendanceList, type PollResult } from "@/lib/api";

export default function AttendanceClient({ deviceId }: { deviceId: string }) {
  const [list, setList] = useState<AttendanceList>({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const [lastPoll, setLastPoll] = useState<PollResult | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.listAttendance(deviceId);
      setList(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [deviceId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onPoll = async () => {
    setPolling(true);
    setError(null);
    try {
      const result = await api.pollDevice(deviceId);
      setLastPoll(result);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPolling(false);
    }
  };

  return (
    <main style={styles.page}>
      <header style={styles.header}>
        <h1>Attendance</h1>
        <button type="button" onClick={onPoll} disabled={polling}>
          {polling ? "Polling…" : "Poll now"}
        </button>
      </header>

      {lastPoll && (
        <p style={styles.info}>
          Polled {lastPoll.polled} record{lastPoll.polled === 1 ? "" : "s"}, {lastPoll.new} new
        </p>
      )}

      {error && <p style={styles.error}>{error}</p>}

      {loading ? (
        <p>Loading…</p>
      ) : list.items.length === 0 ? (
        <p>No attendance records yet. Click &ldquo;Poll now&rdquo; to pull from the device.</p>
      ) : (
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Device user</th>
              <th style={styles.th}>Punched at (UTC)</th>
              <th style={styles.th}>Type</th>
              <th style={styles.th}>Verify mode</th>
            </tr>
          </thead>
          <tbody>
            {list.items.map((item) => (
              <tr key={item.id}>
                <td style={styles.td}>{item.device_user_id}</td>
                <td style={styles.td}>{item.punched_at}</td>
                <td style={styles.td}>{item.punch_type}</td>
                <td style={styles.td}>{item.verify_mode}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { padding: 24, maxWidth: 960, margin: "0 auto", fontFamily: "system-ui" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  info: { padding: "8px 12px", background: "#f3f9f3", borderRadius: 6 },
  error: { color: "crimson" },
  table: { width: "100%", borderCollapse: "collapse", marginTop: 12 },
  th: { textAlign: "left", padding: 8, borderBottom: "2px solid #e5e5e5" },
  td: { padding: 8, borderBottom: "1px solid #f0f0f0" },
};
