import { NextResponse } from "next/server";
import { getAllDocentes } from "../../_lib/docentes";

export const runtime = "nodejs";

export async function GET() {
  try {
    const docentes = await getAllDocentes();
    return NextResponse.json(docentes);
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
