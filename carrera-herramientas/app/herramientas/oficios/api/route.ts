import { NextRequest, NextResponse } from "next/server";
import { renderizarPlantilla } from "../../_lib/docxtemplater";
import { formatearFechaLarga } from "../../_lib/fechas";
import { respuestaDocx } from "../../_lib/respuestaArchivo";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const form = await request.formData();
    const campo = (nombre: string) => (form.get(nombre)?.toString() ?? "").trim();

    const numOficio = campo("num_oficio");
    const contexto = {
      NUM_OFICIO: numOficio,
      FECHA_EMISION: formatearFechaLarga(campo("fecha_emision")),
      CIUDAD: campo("ciudad") || "Manta",
      DESTINATARIO_NOMBRE: campo("destinatario_nombre"),
      DESTINATARIO_CARGO: campo("destinatario_cargo"),
      DESTINATARIO_CARRERA: campo("destinatario_carrera"),
      ASUNTO: campo("asunto"),
      CUERPO: campo("cuerpo"),
      FIRMANTE_TITULO: campo("firmante_titulo"),
      FIRMANTE_NOMBRE: campo("firmante_nombre"),
      FIRMANTE_CARGO: campo("firmante_cargo"),
      INICIALES: campo("iniciales"),
      COPIA_A: campo("copia_a"),
    };

    const buffer = renderizarPlantilla("HOJA_CARRERA_PINE.docx", contexto);
    return respuestaDocx(buffer, `Oficio_${numOficio || "borrador"}.docx`);
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
