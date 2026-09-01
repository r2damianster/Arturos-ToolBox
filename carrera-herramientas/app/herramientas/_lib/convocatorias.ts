import * as XLSX from "xlsx";
import { formatearFechaLarga } from "./fechas";
import type { Docente } from "./docentes";

/** Igual que formatearFechaLarga: convierte 2026-02-20 en "20 de febrero de 2026". */
export const formatearFechaReunion = formatearFechaLarga;

function normalizar(texto: string): string {
  return (texto || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

function detectarFormatoExcel(headers: string[]): "separado" | "completo" {
  if (headers.length < 2) return "completo";
  const normalizados = headers.map(normalizar);
  return normalizados.some((h) => h.includes("apellido")) ? "separado" : "completo";
}

function identificarColumnasNombres(headers: string[]): { idxNombre: number; idxApellido: number } {
  let idxNombre = 0;
  let idxApellido = 1;
  headers.forEach((h, i) => {
    const hLower = h.toLowerCase();
    if (hLower.includes("apellido")) idxApellido = i;
    else if (hLower.includes("nombre")) idxNombre = i;
  });
  return { idxNombre, idxApellido };
}

/** Une varios Excel/HTML de estudiantes, limpia y ordena nombres (sin acentos para el orden). */
export async function procesarExcelEstudiantes(archivos: File[]): Promise<string[]> {
  const consolidados: string[] = [];

  for (const archivo of archivos) {
    try {
      const buffer = Buffer.from(await archivo.arrayBuffer());
      const workbook = XLSX.read(buffer, { type: "buffer" });
      const hojaNombre = workbook.SheetNames[0];
      if (!hojaNombre) continue;
      const filas: unknown[][] = XLSX.utils.sheet_to_json(workbook.Sheets[hojaNombre], {
        header: 1,
        defval: "",
      });
      if (filas.length === 0) continue;

      const headers = (filas[0] as unknown[]).map((h) => String(h ?? ""));
      const formato = detectarFormatoExcel(headers);

      if (formato === "separado") {
        const { idxNombre, idxApellido } = identificarColumnasNombres(headers);
        for (const fila of filas.slice(1)) {
          const nombre = String(fila[idxNombre] ?? "").trim();
          const apellido = String(fila[idxApellido] ?? "").trim();
          const nl = nombre.toLowerCase();
          const al = apellido.toLowerCase();
          if (["nombre", ""].includes(nl) || ["apellido", "apellido(s)", ""].includes(al)) continue;
          if (!(nl + al).includes("nan")) {
            consolidados.push(`${apellido} ${nombre}`.toUpperCase());
          }
        }
      } else {
        for (const fila of filas.slice(1)) {
          const nombreCompleto = String(fila[0] ?? "").trim();
          const nl = nombreCompleto.toLowerCase();
          if (nombreCompleto && nl !== "nombre" && !nl.includes("nan")) {
            consolidados.push(nombreCompleto.toUpperCase());
          }
        }
      }
    } catch {
      continue;
    }
  }

  return Array.from(new Set(consolidados)).sort((a, b) => normalizar(a).localeCompare(normalizar(b)));
}

/** Contexto docxtemplater para la tabla de asistencia de docentes (loop {{#docentes}}). */
export function datosDocentesParaLista(docentes: Docente[]) {
  return docentes.map((d, idx) => ({
    numero: idx + 1,
    cargo: d.cargo,
    nombreCompleto: `${d.titulo_grado} ${d.nombre}, ${d.post_grado}`,
  }));
}

/** Contexto docxtemplater para la tabla de firmas de docentes (2 por fila, loop {{#firmasPares}}). */
export function datosDocentesParaFirmas(docentes: Docente[]) {
  const nombreCompleto = (d: Docente) => `${d.titulo_grado} ${d.nombre}, ${d.post_grado}`;
  const pares: Array<{ izq_nombre: string; izq_cargo: string; der_nombre: string; der_cargo: string }> = [];
  for (let i = 0; i < docentes.length; i += 2) {
    const izq = docentes[i];
    const der = docentes[i + 1];
    pares.push({
      izq_nombre: nombreCompleto(izq),
      izq_cargo: izq.cargo,
      der_nombre: der ? nombreCompleto(der) : "",
      der_cargo: der ? der.cargo : "",
    });
  }
  return pares;
}
