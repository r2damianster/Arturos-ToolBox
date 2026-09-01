import { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType } from "docx";
import { renderizarPlantilla } from "./docxtemplater";
import type { Indicador, Observacion } from "./titulacionLogic";
import { calcularPuntajeTotal } from "./titulacionLogic";
import { PLANTILLA_POR_RUBRICA, type RubricaConSchema } from "./titulacionDb";

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

function fechaLarga(): string {
  const hoy = new Date();
  return `${hoy.getDate()} de ${MESES[hoy.getMonth()]} de ${hoy.getFullYear()}`;
}

interface EvaluacionParaInforme {
  numero_memo: string | null;
  facultad: string | null;
  carrera: string | null;
  opcion_titulacion: string | null;
  titulo_trabajo: string | null;
  tutor: string | null;
  evaluador_nombre: string | null;
  evaluador_correo: string | null;
  observaciones: Observacion[];
}

function celda(texto: string, bold = false): TableCell {
  return new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: texto, bold })] })] });
}

export async function generarInformeDocx(evaluacion: EvaluacionParaInforme): Promise<Buffer> {
  const tutor = evaluacion.tutor || "__________________";
  const opcion = evaluacion.opcion_titulacion || "Trabajo de Integración Curricular o Examen Complexivo";
  const observaciones = evaluacion.observaciones || [];
  const formales = observaciones.filter((o) => o.seccion === "formal");
  const fondo = observaciones.filter((o) => o.seccion === "fondo");

  const tabla1 = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      new TableRow({ children: ["Facultad y/o Extensión", "Carrera", "Opción de Titulación", "Título"].map((t) => celda(t, true)) }),
      new TableRow({
        children: [
          celda(evaluacion.facultad || ""),
          celda(evaluacion.carrera || ""),
          celda(evaluacion.opcion_titulacion || ""),
          celda(evaluacion.titulo_trabajo || ""),
        ],
      }),
    ],
  });

  const filasTabla2: TableRow[] = [
    new TableRow({ children: [celda("Componentes", true), celda("Observaciones", true)] }),
    new TableRow({ children: [celda("Aspectos formales:", true), celda("")] }),
    ...formales.map((o) => new TableRow({ children: [celda(o.componente), celda(o.observacion || "")] })),
    new TableRow({ children: [celda("Aspectos de fondo:", true), celda("")] }),
    ...fondo.map((o) => new TableRow({ children: [celda(o.componente), celda(o.observacion || "")] })),
  ];
  const tabla2 = new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows: filasTabla2 });

  const doc = new Document({
    sections: [
      {
        children: [
          new Paragraph({ children: [new TextRun({ text: `MEMORANDUM No. ${evaluacion.numero_memo || "—"}`, bold: true })] }),
          new Paragraph("PARA: Miembros de Comisión Académica"),
          new Paragraph("ASUNTO: Criterios observados en el trabajo de integración curricular y/o examen complexivo"),
          new Paragraph(`FECHA: Manta, ${fechaLarga()}`),
          new Paragraph(""),
          new Paragraph(
            "En cumplimiento a lo que dispone el Reglamento de Régimen Académico Interno sobre el " +
              "proceso de titulación, una vez que se ha revisado el trabajo de integración curricular " +
              `y/o examen complexivo para el cual fue designado/a en dirigir ${tutor}, de acuerdo al ` +
              "siguiente detalle:"
          ),
          tabla1,
          new Paragraph(""),
          new Paragraph(
            "Luego de haber realizado el análisis en cada uno de los componentes que forman parte del " +
              "trabajo escrito y en concordancia con una de las competencias otorgadas al tribunal de " +
              "titulación —que consiste en que, luego de la revisión del trabajo, éste deberá emitir un " +
              "informe con las observaciones de forma y contenido sobre el documento presentado, el mismo " +
              "que deberá ser conocido por el tutor/a quien direccionará al estudiante para que realice las " +
              `correcciones necesarias— se detallan los criterios del ${opcion} que fueron observados:`
          ),
          tabla2,
          new Paragraph(""),
          new Paragraph("Particular que se informa para los fines consiguientes."),
          new Paragraph(""),
          new Paragraph("Atentamente,"),
          new Paragraph(""),
          new Paragraph(""),
          new Paragraph(evaluacion.evaluador_nombre || "__________________"),
          new Paragraph("Miembro del Tribunal Calificador"),
          new Paragraph(`Correo Electrónico Institucional: ${evaluacion.evaluador_correo || ""}`),
        ],
      },
    ],
  });

  return Packer.toBuffer(doc);
}

interface EvaluacionParaRubrica {
  estudiante: string | null;
  evaluador_nombre: string | null;
  tutor: string | null;
  titulo_trabajo: string | null;
  rubrica: RubricaConSchema;
  indicadores: Indicador[];
  puntaje_total: number;
}

function indicadoresPorClave(indicadores: Indicador[]): Map<string, Indicador> {
  const mapa = new Map<string, Indicador>();
  for (const i of indicadores) mapa.set(`${i.tabla_idx}:${i.criterio_idx}`, i);
  return mapa;
}

export function generarRubricaDocx(evaluacion: EvaluacionParaRubrica): Buffer {
  const { rubrica, indicadores, puntaje_total: puntajeTotal } = evaluacion;
  const schema = rubrica.schema;
  const tabla = schema.tablas[0];
  const escala = tabla.escala;
  const indicadoresMapa = indicadoresPorClave(indicadores || []);
  const escalaTotal = schema.escala_total ?? 10;
  const puntajeFormateado = puntajeTotal.toFixed(2);

  const contexto: Record<string, unknown> = {
    ESTUDIANTE_LINEA: `NOMBRE DEL/LA ESTUDIANTE: ${evaluacion.estudiante || ""}`,
    EVALUADOR_LINEA: `NOMBRE DEL MIEMBRO DEL TRIBUNAL: ${evaluacion.evaluador_nombre || ""}`,
    TUTOR_LINEA: `TUTOR: ${evaluacion.tutor || ""}`,
    TEMA_LINEA: `TÍTULO DEL ARTÍCULO: ${evaluacion.titulo_trabajo || ""}`,
    FECHA_LINEA:
      escala === "peso_si_no" || escala === "si_no"
        ? `Fecha: ${fechaLarga()}                 Calificación Total: ${puntajeFormateado} / ${escalaTotal}`
        : `FECHA DE ENTREGA: ${fechaLarga()}`,
    TOTAL_SCORE: puntajeFormateado,
  };

  tabla.criterios.forEach((_criterio, criterioIdx) => {
    const indicador = indicadoresMapa.get(`0:${criterioIdx}`);
    const respuesta = indicador?.respuesta ?? null;
    const calificacion = indicador?.calificacion ?? null;
    const comentario = indicador?.comentario || "";
    const score = calificacion != null ? Number(calificacion).toFixed(2) : "";

    if (escala === "peso_si_no" || escala === "si_no") {
      contexto[`c${criterioIdx}_yes`] = respuesta === "YES" ? "X" : "";
      contexto[`c${criterioIdx}_no`] = respuesta === "NO" ? "X" : "";
      contexto[`c${criterioIdx}_score`] = score;
    } else {
      contexto[`c${criterioIdx}_mark0`] = respuesta === "0" ? "[X] " : "";
      contexto[`c${criterioIdx}_mark35`] = respuesta === "35" ? "[X] " : "";
      contexto[`c${criterioIdx}_mark70`] = respuesta === "70" || respuesta === "90" ? "[X] " : "";
      contexto[`c${criterioIdx}_mark100`] = respuesta === "100" ? "[X] " : "";
      contexto[`c${criterioIdx}_score`] = score;
      contexto[`c${criterioIdx}_comment`] = comentario;
    }
  });

  const nombrePlantilla = PLANTILLA_POR_RUBRICA[rubrica.slug];
  if (!nombrePlantilla) throw new Error(`No hay plantilla configurada para la rúbrica "${rubrica.slug}"`);
  return renderizarPlantilla(nombrePlantilla, contexto);
}

export { calcularPuntajeTotal };
