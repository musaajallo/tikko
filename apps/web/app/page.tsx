import Link from "next/link";

export default function Home() {
  return (
    <main>
      <h1>tikko</h1>
      <p>ZKTeco terminal management.</p>
      <nav>
        <Link href="/devices">Devices</Link>
      </nav>
    </main>
  );
}
