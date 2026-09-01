import { NextRequest, NextResponse } from "next/server";
import { crearDocxActa, generarTextoIA, formatearFechaActa } from "../../_lib/actaTecnica";
import { respuestaDocx } from "../../_lib/respuestaArchivo";

export const runtime = "nodejs";

function tipoImagen(nombreArchivo: string): "png" | "jpg" {
  return nombreArchivo.toLowerCase().endsWith(".png") ? "png" : "jpg";
}

export async function POST(request: NextRequest) {
  try {
    const form = await request.formData();
    const campo = (nombre: string) => (form.get(nombre)?.toString() ?? "").trim();

    const convocanteRaw = campo("convocante");
    const [convocanteNombre = "Convocante", convocanteCargo = ""] = convocanteRaw.split(",").map((s) => s.trim());

    const titulos = form.getAll("p_titulo[]").map(String);
    const nombres = form.getAll("p_nombre[]").map(String);
    const apellidos = form.getAll("p_apellido[]").map(String);
    const cargos = form.getAll("p_cargo[]").map(String);
    const participantes = nombres
      .map((nombre, i) => ({
        nombre: `${titulos[i] ?? ""} ${nombre} ${apellidos[i] ?? ""}`.trim(),
        cargo: cargos[i] || "Docente",
      }))
      .filter((p) => p.nombre);

    const [aspectosIA, desarrolloIA, compromisosIA] = await Promise.all([
      generarTextoIA("aspectos", campo("notas_aspectos")),
      generarTextoIA("desarrollo", campo("notas_reunion")),
      generarTextoIA("compromisos", campo("notas_compromisos")),
    ]);

    const archivosFoto = form.getAll("fotos_evidencia").filter((f): f is File => f instanceof File && f.size > 0);
    const fotos = await Promise.all(
      archivosFoto.map(async (f) => ({
        buffer: Buffer.from(await f.arrayBuffer()),
        tipo: tipoImagen(f.name),
      }))
    );

    const buffer = await crearDocxActa(
      {
        numeroActa: campo("num_acta"),
        fechaLarga: formatearFechaActa(campo("fecha_reunion")),
        lugar: campo("lugar_reunion") || "Instalaciones Institucionales",
        horaInicio: campo("hora_inicio") || "--:--",
        horaFin: campo("hora_fin") || "--:--",
        convocanteNombre,
        convocanteCargo,
        participantes,
        aspectosIA,
        desarrolloIA,
        compromisosIA,
        elaboradoTitulo: campo("elaborado_titulo"),
        elaboradoNombre: campo("elaborado_nombre"),
      },
      fotos
    );

    const numero = (campo("num_acta") || "000").replace(/\//g, "-");
    return respuestaDocx(buffer, `Acta_${numero}.docx`);
  } catch (error) {
    const mensaje = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: mensaje }, { status: 500 });
  }
}
