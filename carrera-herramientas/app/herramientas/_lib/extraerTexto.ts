import { PDFParse } from "pdf-parse";
import mammoth from "mammoth";

/** Extrae texto plano de un PDF o DOCX (bytes en memoria). Lanza si el formato no es soportado. */
export async function extraerTexto(nombreArchivo: string, contenido: Buffer): Promise<string> {
  const nombre = (nombreArchivo || "").toLowerCase();
  if (nombre.endsWith(".pdf")) {
    const parser = new PDFParse({ data: contenido });
    try {
      const resultado = await parser.getText();
      return resultado.text;
    } finally {
      await parser.destroy();
    }
  }
  if (nombre.endsWith(".docx")) {
    const resultado = await mammoth.extractRawText({ buffer: contenido });
    return resultado.value;
  }
  throw new Error("Formato no soportado para extracción de texto (use PDF o DOCX).");
}
