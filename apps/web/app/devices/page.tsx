"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Device } from "@tikko/shared-types";

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [host, setHost] = useState("");
  const [port, setPort] = useState("4370");
  const [submitting, setSubmitting] = useState(false);

  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, string>>({});

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { items } = await api.listDevices();
      setDevices(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createDevice({
        name,
        host,
        port: Number(port) || 4370,
      });
      setName("");
      setHost("");
      setPort("4370");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  const onTestConnection = async (deviceId: string) => {
    setTestingId(deviceId);
    try {
      const info = await api.testConnection(deviceId);
      setTestResult((prev) => ({
        ...prev,
        [deviceId]: `${info.device_name} (${info.serial_number}) firmware ${info.firmware_version}`,
      }));
    } catch (err) {
      setTestResult((prev) => ({
        ...prev,
        [deviceId]: err instanceof Error ? err.message : String(err),
      }));
    } finally {
      setTestingId(null);
    }
  };

  return (
    <main style={styles.page}>
      <h1>Devices</h1>

      <form onSubmit={onSubmit} style={styles.form}>
        <input
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          placeholder="Host (IP)"
          value={host}
          onChange={(e) => setHost(e.target.value)}
          required
        />
        <input
          placeholder="Port"
          value={port}
          onChange={(e) => setPort(e.target.value)}
          inputMode="numeric"
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Adding…" : "Add device"}
        </button>
      </form>

      {error && <p style={styles.error}>{error}</p>}

      {loading ? (
        <p>Loading devices…</p>
      ) : devices.length === 0 ? (
        <p>No devices yet. Add one above.</p>
      ) : (
        <ul style={styles.list}>
          {devices.map((d) => (
            <li key={d.id} style={styles.item}>
              <div>
                <strong>{d.name}</strong>
                <div>
                  {d.host}:{d.port}
                </div>
                {d.location && <small>{d.location}</small>}
                {testResult[d.id] && (
                  <p style={styles.testResult}>{testResult[d.id]}</p>
                )}
              </div>
              <div style={styles.actions}>
                <button
                  type="button"
                  onClick={() => onTestConnection(d.id)}
                  disabled={testingId === d.id}
                >
                  {testingId === d.id ? "Testing…" : "Test connection"}
                </button>
                <Link href={`/devices/${d.id}/attendance`}>
                  View attendance →
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { padding: 24, maxWidth: 760, margin: "0 auto", fontFamily: "system-ui" },
  form: { display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" },
  list: { listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: 12 },
  item: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    padding: 12,
    border: "1px solid #e5e5e5",
    borderRadius: 8,
  },
  actions: { display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-end" },
  testResult: { marginTop: 8, fontSize: 13, opacity: 0.8 },
  error: { color: "crimson" },
};
