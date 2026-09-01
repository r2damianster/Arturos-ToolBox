import { NextRequest, NextResponse } from "next/server";
import { extraerTexto } from "../../../_lib/extraerTexto";
import { precargarDatosMemo } from "../../../_lib/titulacionIa";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const form = await request.formData();
    const archivo = form.get("archivo");
    if (!(archivo instanceof File) || !archivo.size) {
      return NextResponse.json({ error: "No se recibió ningún archivo." }, { status: 400 });
    }

    const buffer = Buffer.from(await archivo.arrayBuffer());
    const texto = await extraerTexto(archivo.name, buffer);
    const [datos, error] = await precargarDatosMemo(texto);
    if (error) return NextResponse.json({ error }, { status: 500 });
    return NextResponse.json(datos);
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 400 });
  }
}
