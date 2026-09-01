import { NextResponse } from "next/server";
import { getAllCarreras } from "../../../_lib/docentes";

export const runtime = "nodejs";

export async function GET() {
  try {
    const carreras = await getAllCarreras();
    return NextResponse.json(carreras);
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
