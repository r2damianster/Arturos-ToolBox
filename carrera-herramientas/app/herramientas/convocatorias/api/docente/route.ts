import { NextRequest, NextResponse } from "next/server";
import { renderizarPlantilla } from "../../../_lib/docxtemplater";
import { formatearFechaLarga } from "../../../_lib/fechas";
import { datosDocentesParaLista, datosDocentesParaFirmas } from "../../../_lib/convocatorias";
import { getAllDocentes, type Docente } from "../../../_lib/docentes";
import { respuestaDocx } from "../../../_lib/respuestaArchivo";

export const runtime = "nodejs";

interface DocenteManual {
  titulo?: string;
  titulo_grado?: string;
  nombre?: string;
  postgrado?: string;
  post_grado?: string;
  cargo?: string;
}

export async function POST(request: NextRequest) {
  try {
    const form = await request.formData();
    const campo = (nombre: string) => (form.get(nombre)?.toString() ?? "").trim();

    const contexto: Record<string, string> = {
      NUM_CONVOCATORIA: campo("num_convocatoria"),
      PERIODO: campo("periodo"),
      SIGLAS_CONVOCANTE: "PINE",
      CIUDAD: campo("ciudad"),
      FECHA_LARGA: formatearFechaLarga(campo("fecha_larga")),
      ASUNTO: campo("asunto"),
      DESCRIPCION_CONVOCATORIA: campo("descripcion_convocatoria"),
      FECHA_REUNION: formatearFechaLarga(campo("fecha_reunion")),
      HORA_REUNION: campo("hora_reunion"),
      LUGAR_REUNION: campo("lugar_reunion"),
      CONVOCANTE_TITULO: campo("convocante_titulo"),
      CONVOCANTE_NOMBRE: campo("convocante_nombre"),
      CONVOCANTE_CARGO: campo("convocante_cargo"),
      INICIALES_ELABORADOR: campo("iniciales_elaborador"),
    };

    const modo = campo("modo_docentes") || "carrera";
    let docentes: Docente[];
    if (modo === "manual") {
      const docentesJson = campo("docentes_json");
      const manuales: DocenteManual[] = docentesJson ? JSON.parse(docentesJson) : [];
      docentes = manuales.map((d) => ({
        id: 0,
        titulo_grado: d.titulo || d.titulo_grado || "Lic.",
        nombre: d.nombre || "",
        post_grado: d.postgrado || d.post_grado || "",
        cargo: d.cargo || "Docente",
        carrera: "",
        es_director: false,
      }));
    } else {
      docentes = await getAllDocentes();
    }

    const buffer = renderizarPlantilla("Convocatoria_Docentes.docx", {
      ...contexto,
      docentes: datosDocentesParaLista(docentes),
      firmasPares: datosDocentesParaFirmas(docentes),
    });

    return respuestaDocx(buffer, "Convocatoria_Docentes.docx");
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
