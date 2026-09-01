import { NextRequest, NextResponse } from "next/server";
import { extraerTexto } from "../../../../../_lib/extraerTexto";
import { EXTENSIONES_PERMITIDAS, guardarTextoExtraido } from "../../../../../_lib/titulacionLogic";

export const runtime = "nodejs";

/**
 * Recibe el memo o el trabajo del estudiante (PDF/DOCX), extrae su texto y lo guarda
 * en la evaluación. El archivo en sí nunca se persiste — solo el texto extraído.
 */
export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const form = await request.formData();
    const tipo = form.get("tipo")?.toString();
    const archivo = form.get("archivo");

    if (tipo !== "memo" && tipo !== "trabajo") {
      return NextResponse.json({ error: "tipo debe ser 'memo' o 'trabajo'" }, { status: 400 });
    }
    if (!(archivo instanceof File) || !archivo.size) {
      return NextResponse.json({ error: "No se recibió ningún archivo." }, { status: 400 });
    }
    const extension = archivo.name.toLowerCase().slice(archivo.name.lastIndexOf("."));
    if (!EXTENSIONES_PERMITIDAS.includes(extension)) {
      return NextResponse.json({ error: `Extensión no permitida: ${extension}. Use PDF o Word.` }, { status: 400 });
    }

    const buffer = Buffer.from(await archivo.arrayBuffer());
    const texto = await extraerTexto(archivo.name, buffer);
    await guardarTextoExtraido(Number(params.id), tipo, texto);

    return NextResponse.json({ ok: true });
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
