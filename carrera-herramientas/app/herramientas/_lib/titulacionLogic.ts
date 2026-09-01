import { sql } from "./db";
import { calcularFechaLimite } from "./fechas";
import { COMPONENTES_INFORME, getRubrica, type RubricaConSchema } from "./titulacionDb";

export interface Evaluacion {
  id: number;
  numero_memo: string | null;
  fecha_memo: string | null;
  fecha_limite: string | null;
  facultad: string | null;
  carrera: string | null;
  opcion_titulacion: string | null;
  titulo_trabajo: string | null;
  estudiante: string | null;
  tutor: string | null;
  evaluador_nombre: string | null;
  evaluador_correo: string | null;
  modalidad_id: number | null;
  rubrica_id: number | null;
  texto_memo: string | null;
  texto_trabajo: string | null;
  estado: string;
}

export interface Indicador {
  id?: number;
  evaluacion_id?: number;
  tabla_idx: number;
  criterio_idx: number;
  criterio_texto: string;
  peso: number;
  respuesta: string | null;
  calificacion: number | null;
  comentario: string;
  sugerencia_ia: string | null;
}

export interface Observacion {
  id: number;
  evaluacion_id: number;
  seccion: "formal" | "fondo";
  componente: string;
  observacion: string;
}

export interface DatosMemo {
  numero_memo?: string;
  fecha_memo?: string;
  facultad?: string;
  carrera?: string;
  opcion_titulacion?: string;
  titulo_trabajo?: string;
  estudiante?: string;
  tutor?: string;
  evaluador_nombre?: string;
  evaluador_correo?: string;
  modalidad_id?: number;
  rubrica_id?: number;
}

export async function listarModalidadesConRubricas() {
  const modalidades = await sql`SELECT * FROM modalidades_titulacion ORDER BY id`;
  const resultado = [];
  for (const m of modalidades as Array<{ id: number; slug: string; nombre: string; requiere_subtipo: boolean }>) {
    const rubricas = await sql`SELECT id, slug, subtipo FROM rubricas WHERE modalidad_id = ${m.id} ORDER BY id`;
    resultado.push({ ...m, rubricas });
  }
  return resultado;
}

export async function crearEvaluacion(datos: DatosMemo): Promise<number> {
  const fechaMemo = datos.fecha_memo?.trim() || null;
  const fechaLimite = fechaMemo ? calcularFechaLimite(fechaMemo) : null;

  const [fila] = await sql`
    INSERT INTO evaluaciones (
      numero_memo, fecha_memo, fecha_limite, facultad, carrera,
      opcion_titulacion, titulo_trabajo, estudiante, tutor,
      evaluador_nombre, evaluador_correo, modalidad_id, rubrica_id, estado
    ) VALUES (
      ${datos.numero_memo || ""}, ${fechaMemo}, ${fechaLimite}, ${datos.facultad || ""}, ${datos.carrera || ""},
      ${datos.opcion_titulacion || ""}, ${datos.titulo_trabajo || ""}, ${datos.estudiante || ""}, ${datos.tutor || ""},
      ${datos.evaluador_nombre || ""}, ${datos.evaluador_correo || ""}, ${datos.modalidad_id ?? null}, ${datos.rubrica_id ?? null}, 'borrador'
    ) RETURNING id
  `;
  const evaluacionId = fila.id as number;

  for (const componente of COMPONENTES_INFORME.formales) {
    await sql`INSERT INTO evaluacion_observaciones (evaluacion_id, seccion, componente) VALUES (${evaluacionId}, 'formal', ${componente})`;
  }
  for (const componente of COMPONENTES_INFORME.fondo) {
    await sql`INSERT INTO evaluacion_observaciones (evaluacion_id, seccion, componente) VALUES (${evaluacionId}, 'fondo', ${componente})`;
  }

  return evaluacionId;
}

export async function actualizarModalidad(evaluacionId: number, modalidadId: number, rubricaId: number): Promise<void> {
  await sql`
    UPDATE evaluaciones SET modalidad_id = ${modalidadId}, rubrica_id = ${rubricaId}, actualizado_en = now()
    WHERE id = ${evaluacionId}
  `;
}

export async function obtenerEvaluacion(evaluacionId: number): Promise<(Evaluacion & { rubrica?: RubricaConSchema | null }) | null> {
  const rows = await sql`SELECT * FROM evaluaciones WHERE id = ${evaluacionId}`;
  const evaluacion = (rows as Evaluacion[])[0];
  if (!evaluacion) return null;
  if (evaluacion.rubrica_id) {
    return { ...evaluacion, rubrica: await getRubrica(evaluacion.rubrica_id) };
  }
  return evaluacion;
}

/** Extensiones permitidas para memo/trabajo del par lector. No se guarda el archivo: solo el texto extraído. */
export const EXTENSIONES_PERMITIDAS = [".pdf", ".docx", ".doc"];

export async function guardarTextoExtraido(evaluacionId: number, tipo: "memo" | "trabajo", texto: string): Promise<void> {
  if (tipo === "memo") {
    await sql`UPDATE evaluaciones SET texto_memo = ${texto}, actualizado_en = now() WHERE id = ${evaluacionId}`;
  } else {
    await sql`UPDATE evaluaciones SET texto_trabajo = ${texto}, actualizado_en = now() WHERE id = ${evaluacionId}`;
  }
}

export async function obtenerDetalleEvaluacion(evaluacionId: number) {
  const evaluacion = await obtenerEvaluacion(evaluacionId);
  if (!evaluacion) return null;

  const indicadores = await sql`
    SELECT * FROM evaluacion_indicadores WHERE evaluacion_id = ${evaluacionId} ORDER BY tabla_idx, criterio_idx
  `;
  const observaciones = await sql`
    SELECT * FROM evaluacion_observaciones WHERE evaluacion_id = ${evaluacionId} ORDER BY id
  `;

  const detalle = {
    ...evaluacion,
    indicadores: indicadores as Indicador[],
    observaciones: observaciones as Observacion[],
    puntaje_total: 0,
  };
  if (evaluacion.rubrica) {
    detalle.puntaje_total = calcularPuntajeTotal(evaluacion.rubrica.schema, detalle.indicadores);
  }
  return detalle;
}

export function calcularPuntajeTotal(schema: { tabla_total_idx?: number }, indicadores: Indicador[]): number {
  const tablaTotalIdx = schema.tabla_total_idx ?? 0;
  let total = 0;
  for (const indicador of indicadores) {
    if (indicador.tabla_idx !== tablaTotalIdx) continue;
    if (indicador.calificacion != null) total += Number(indicador.calificacion);
  }
  return Math.round(total * 100) / 100;
}

export async function guardarIndicadores(evaluacionId: number, indicadores: Indicador[]): Promise<void> {
  await sql`DELETE FROM evaluacion_indicadores WHERE evaluacion_id = ${evaluacionId}`;
  for (const ind of indicadores) {
    await sql`
      INSERT INTO evaluacion_indicadores (
        evaluacion_id, tabla_idx, criterio_idx, criterio_texto, peso,
        respuesta, calificacion, comentario, sugerencia_ia
      ) VALUES (
        ${evaluacionId}, ${ind.tabla_idx}, ${ind.criterio_idx}, ${ind.criterio_texto || ""}, ${ind.peso || 0},
        ${ind.respuesta ?? null}, ${ind.calificacion ?? null}, ${ind.comentario || ""}, ${ind.sugerencia_ia ?? null}
      )
    `;
  }
}

export async function guardarObservaciones(evaluacionId: number, observaciones: Array<{ id: number; observacion?: string }>): Promise<void> {
  for (const obs of observaciones) {
    if (!obs.id) continue;
    await sql`
      UPDATE evaluacion_observaciones SET observacion = ${obs.observacion || ""}
      WHERE id = ${obs.id} AND evaluacion_id = ${evaluacionId}
    `;
  }
}

export async function marcarFinalizada(evaluacionId: number): Promise<void> {
  await sql`UPDATE evaluaciones SET estado = 'finalizada', actualizado_en = now() WHERE id = ${evaluacionId}`;
}
