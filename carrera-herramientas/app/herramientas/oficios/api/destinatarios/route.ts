import { NextRequest, NextResponse } from "next/server";
import { getAllDocentes, getDocentesByCarrera } from "../../../_lib/docentes";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  try {
    const carrera = request.nextUrl.searchParams.get("carrera");
    const destinatarios = carrera ? await getDocentesByCarrera(carrera) : await getAllDocentes();
    return NextResponse.json(destinatarios);
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
