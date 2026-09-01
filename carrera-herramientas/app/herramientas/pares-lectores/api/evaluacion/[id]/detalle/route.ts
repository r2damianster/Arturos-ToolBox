import { NextRequest, NextResponse } from "next/server";
import { obtenerDetalleEvaluacion } from "../../../../../_lib/titulacionLogic";

export const runtime = "nodejs";

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const detalle = await obtenerDetalleEvaluacion(Number(params.id));
    if (!detalle) return NextResponse.json({ error: "Evaluación no encontrada" }, { status: 404 });
    return NextResponse.json(detalle);
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
