import { NextRequest, NextResponse } from "next/server";
import { guardarObservaciones } from "../../../../../_lib/titulacionLogic";

export const runtime = "nodejs";

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const observaciones = await request.json();
    await guardarObservaciones(Number(params.id), Array.isArray(observaciones) ? observaciones : []);
    return NextResponse.json({ ok: true });
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
