import { NextRequest, NextResponse } from "next/server";
import { obtenerDetalleEvaluacion, marcarFinalizada } from "../../../../../_lib/titulacionLogic";
import { generarInformeDocx, generarRubricaDocx } from "../../../../../_lib/titulacionDocgen";
import { crearZip } from "../../../../../_lib/zip";
import { respuestaZip } from "../../../../../_lib/respuestaArchivo";

export const runtime = "nodejs";

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const evaluacionId = Number(params.id);
    const evaluacion = await obtenerDetalleEvaluacion(evaluacionId);
    if (!evaluacion) {
      return NextResponse.json({ error: "Evaluación no encontrada" }, { status: 404 });
    }
    if (!evaluacion.rubrica) {
      return NextResponse.json({ error: "Falta seleccionar la modalidad/rúbrica antes de generar los documentos." }, { status: 400 });
    }

    const [informeBuffer, rubricaBuffer] = await Promise.all([
      generarInformeDocx(evaluacion),
      Promise.resolve(generarRubricaDocx({ ...evaluacion, rubrica: evaluacion.rubrica })),
    ]);

    const slugTitulo = (evaluacion.titulo_trabajo || "evaluacion")
      .replace(/[^A-Za-z0-9]+/g, "_")
      .replace(/^_|_$/g, "")
      .slice(0, 40);

    const zipBuffer = await crearZip([
      { nombre: `Informe_Criterios_Observados_${slugTitulo}.docx`, buffer: informeBuffer },
      { nombre: `Rubrica_${slugTitulo}.docx`, buffer: rubricaBuffer },
    ]);

    await marcarFinalizada(evaluacionId);

    return respuestaZip(zipBuffer, `Evaluacion_${evaluacionId}_${slugTitulo}.zip`);
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
