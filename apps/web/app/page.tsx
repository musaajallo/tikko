import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1>tikko</h1>
      <p>ZKTeco terminal management.</p>
      <nav style={{ display: "flex", gap: 12 }}>
        <Link href="/devices">Devices</Link>
        <Link href="/login">Sign in</Link>
      </nav>
    </main>
  );
}
