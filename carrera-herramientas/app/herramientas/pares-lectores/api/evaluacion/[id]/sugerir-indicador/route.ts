import { NextRequest, NextResponse } from "next/server";
import { obtenerEvaluacion } from "../../../../../_lib/titulacionLogic";
import { sugerirComentarioCriterio } from "../../../../../_lib/titulacionIa";

export const runtime = "nodejs";

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const datos = await request.json();
    const criterioTexto = (datos.criterio_texto || "").trim();
    if (!criterioTexto) {
      return NextResponse.json({ error: "Falta 'criterio_texto'." }, { status: 400 });
    }

    const evaluacion = await obtenerEvaluacion(Number(params.id));
    if (!evaluacion) return NextResponse.json({ error: "Evaluación no encontrada" }, { status: 404 });
    if (!evaluacion.texto_trabajo) {
      return NextResponse.json({ error: "Esta evaluación no tiene un archivo de trabajo subido todavía." }, { status: 400 });
    }

    const [sugerencia, error] = await sugerirComentarioCriterio(criterioTexto, evaluacion.texto_trabajo);
    if (error) return NextResponse.json({ error }, { status: 500 });
    return NextResponse.json({ sugerencia });
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
