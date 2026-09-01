import { NextRequest, NextResponse } from "next/server";
import { enriquecerTexto } from "../../_lib/enriquecerTexto";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const data = await request.json().catch(() => ({}));
  const contexto = (data.contexto || "").trim();
  const texto = (data.texto || "").trim();
  const tono = (data.tono || "").trim();

  if (!contexto || !texto) {
    return NextResponse.json({ error: "Se requiere 'contexto' y 'texto'" }, { status: 400 });
  }

  const [resultado, error] = await enriquecerTexto(contexto, texto, tono || undefined);
  if (error) {
    return NextResponse.json({ error }, { status: 500 });
  }
  return NextResponse.json({ texto_enriquecido: resultado });
}
