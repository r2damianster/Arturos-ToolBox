import { NextRequest, NextResponse } from "next/server";
import { renderizarPlantilla } from "../../../_lib/docxtemplater";
import { formatearFechaLarga } from "../../../_lib/fechas";
import { procesarExcelEstudiantes } from "../../../_lib/convocatorias";
import { respuestaDocx } from "../../../_lib/respuestaArchivo";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const form = await request.formData();
    const campo = (nombre: string) => (form.get(nombre)?.toString() ?? "").trim();
    const cursos = form.getAll("cursos").map((c) => c.toString());

    const contexto: Record<string, string> = {
      NUM_CONVOCATORIA: campo("num_convocatoria"),
      PERIODO: campo("periodo"),
      SIGLAS_CONVOCANTE: "PINE",
      CIUDAD: campo("ciudad"),
      FECHA_LARGA: formatearFechaLarga(campo("fecha_larga")),
      ASUNTO: campo("asunto"),
      CURSO: cursos.join(", "),
      DESCRIPCION_CONVOCATORIA: campo("descripcion_convocatoria"),
      FECHA_REUNION: formatearFechaLarga(campo("fecha_reunion")),
      HORA_REUNION: campo("hora_reunion"),
      LUGAR_REUNION: campo("lugar_reunion"),
      CONVOCANTE_TITULO: campo("convocante_titulo"),
      CONVOCANTE_NOMBRE: campo("convocante_nombre"),
      CONVOCANTE_CARGO: campo("convocante_cargo"),
      INICIALES_ELABORADOR: campo("iniciales_elaborador"),
    };

    const archivosExcel = form.getAll("excel_files").filter((f): f is File => f instanceof File && f.size > 0);
    const estudiantes = archivosExcel.length > 0 ? await procesarExcelEstudiantes(archivosExcel) : [];

    const buffer = renderizarPlantilla("Convocatoria_Estudiantes.docx", {
      ...contexto,
      estudiantes,
    });

    return respuestaDocx(buffer, "Convocatoria_Estudiantes.docx");
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
