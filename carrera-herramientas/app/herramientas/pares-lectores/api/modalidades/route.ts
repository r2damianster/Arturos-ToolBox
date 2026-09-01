import { NextResponse } from "next/server";
import { listarModalidadesConRubricas } from "../../../_lib/titulacionLogic";

export const runtime = "nodejs";

export async function GET() {
  try {
    return NextResponse.json(await listarModalidadesConRubricas());
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
