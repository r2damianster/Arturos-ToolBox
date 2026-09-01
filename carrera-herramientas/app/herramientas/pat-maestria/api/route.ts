import { NextRequest, NextResponse } from "next/server";
import { prepararDatosParaPats, generarDocumentosPats } from "../../_lib/patMaestria";
import { crearZip } from "../../_lib/zip";
import { respuestaZip } from "../../_lib/respuestaArchivo";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const form = await request.formData();
    const datos = prepararDatosParaPats(form);
    const documentos = generarDocumentosPats(datos);
    const zipBuffer = await crearZip(documentos);
    const nombreDescarga = `PATS_${(datos.nombre || "maestrante").replace(/\s+/g, "_").slice(0, 15)}.zip`;
    return respuestaZip(zipBuffer, nombreDescarga);
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
