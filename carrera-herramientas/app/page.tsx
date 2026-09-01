import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: 40 }}>
      <p>Andamiaje de desarrollo — no se pega en el destino.</p>
      <Link href="/herramientas">Ir a /herramientas →</Link>
    </main>
  );
}
