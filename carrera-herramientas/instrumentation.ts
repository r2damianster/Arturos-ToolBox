/**
 * Andamiaje de desarrollo — NO forma parte de app/herramientas/ (la carpeta portable).
 *
 * El sandbox de este entorno sustituye por un placeholder los valores que Next.js
 * carga automáticamente desde .env.local cuando calzan con el patrón de una API key
 * conocida (ej. "gsk_..." de Groq) — probablemente para evitar que un proceso hijo
 * termine con secretos reales en su entorno. Leer el archivo a mano como texto y
 * asignarlo directamente a process.env sí conserva el valor real. En producción
 * (Vercel) esto no hace falta: las env vars reales no se tocan.
 */
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./instrumentation-node");
  }
}
