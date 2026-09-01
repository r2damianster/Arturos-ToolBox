import { NextRequest, NextResponse } from "next/server";
import { guardarIndicadores } from "../../../../../_lib/titulacionLogic";

export const runtime = "nodejs";

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const indicadores = await request.json();
    await guardarIndicadores(Number(params.id), Array.isArray(indicadores) ? indicadores : []);
    return NextResponse.json({ ok: true });
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
