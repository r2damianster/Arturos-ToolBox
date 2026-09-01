import {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, ImageRun, WidthType, BorderStyle, PageBreak,
} from "docx";
import { pedirCompletionIA, formatearErrorIA } from "./groq";
import { formatearFechaLarga } from "./fechas";

interface Participante {
  nombre: string;
  cargo: string;
}

interface Firmante {
  nombre: string;
  cargo: string;
}

export interface DatosActa {
  numeroActa: string;
  fechaLarga: string;
  lugar: string;
  horaInicio: string;
  horaFin: string;
  convocanteNombre: string;
  convocanteCargo: string;
  participantes: Participante[];
  aspectosIA: string;
  desarrolloIA: string;
  compromisosIA: string;
  elaboradoTitulo: string;
  elaboradoNombre: string;
}

const PROMPTS_ACTA: Record<"aspectos" | "desarrollo" | "compromisos", { seccion: string; instruccion: string; temperature: number }> = {
  aspectos: {
    seccion: "Puntos del orden del día",
    instruccion:
      "TAREA: Organiza los puntos del orden del día.\n" +
      "REGLAS: No expandas el texto innecesariamente. Solo corrige ortografía y formaliza levemente el vocabulario.\n" +
      "FORMATO: Presenta cada punto precedido por una viñeta (•). No redactes párrafos largos.",
    temperature: 0.2,
  },
  compromisos: {
    seccion: "Decisiones y compromisos finales",
    instruccion:
      "TAREA: Redacta los acuerdos y compromisos institucionales.\n" +
      "REGLAS: Sé directo y breve. Mantén la esencia de la nota original sin añadir relleno.\n" +
      "FORMATO: Presenta cada compromiso precedido por una viñeta (•). Corrige coherencia y ortografía.",
    temperature: 0.2,
  },
  desarrollo: {
    seccion: "Desarrollo y deliberaciones de la reunión",
    instruccion:
      "TAREA: Convierte las notas en un relato académico fluido y profesional.\n" +
      "REGLAS: Aquí SÍ puedes expandirte. Conecta los puntos del orden del día con conectores lógicos.\n" +
      "FORMATO: Redacta en párrafos narrativos. Usa tono solemne (ej: 'asimismo', 'se procedió a').",
    temperature: 0.5,
  },
};

/** Redacta cada sección del acta con IA a partir de las notas del usuario. Siempre se ejecuta al generar (igual que logic/actas_logic.py:generar_texto_ia). */
export async function generarTextoIA(tipo: "aspectos" | "desarrollo" | "compromisos", notasUsuario: string): Promise<string> {
  if (!notasUsuario || notasUsuario.trim().length < 2) {
    return "No se registraron detalles adicionales para esta sección.";
  }
  if (!process.env.GROQ_API_KEY) {
    return `[IA no configurada] ${notasUsuario}`;
  }

  const config = PROMPTS_ACTA[tipo];
  const prompt =
    `Actúa como un Secretario Académico universitario de alto nivel.\n\n` +
    `SECCIÓN: ${config.seccion}.\n${config.instruccion}\n\n` +
    `NOTAS DEL USUARIO:\n${notasUsuario}`;

  try {
    const resultado = await pedirCompletionIA(
      [
        { role: "system", content: "Eres un redactor experto que diferencia entre listas breves y desarrollo narrativo." },
        { role: "user", content: prompt },
      ],
      { temperature: config.temperature, reasoningEffort: "low" }
    );
    return resultado.replace(/\*\*/g, "").replace(/\*/g, "•");
  } catch (e) {
    return `${formatearErrorIA(e)} (notas originales: ${notasUsuario})`;
  }
}

function celdaEtiqueta(texto: string): TableCell {
  return new TableCell({
    width: { size: 30, type: WidthType.PERCENTAGE },
    children: [new Paragraph({ children: [new TextRun({ text: texto, bold: true })] })],
  });
}

function celdaValor(lineas: string[]): TableCell {
  return new TableCell({
    width: { size: 70, type: WidthType.PERCENTAGE },
    children: lineas.map((linea) => new Paragraph(linea)),
  });
}

const SIN_BORDES = {
  top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  insideHorizontal: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  insideVertical: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
};

export async function crearDocxActa(datos: DatosActa, fotos: Array<{ buffer: Buffer; tipo: "png" | "jpg" }>): Promise<Buffer> {
  const firmantes: Firmante[] = [
    { nombre: datos.convocanteNombre, cargo: datos.convocanteCargo },
    ...datos.participantes.slice(0, 9),
  ];
  while (firmantes.length < 10) firmantes.push({ nombre: "", cargo: "" });

  const children: Array<Paragraph | Table> = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      heading: HeadingLevel.TITLE,
      children: [new TextRun({ text: "UNIVERSIDAD LAICA ELOY ALFARO DE MANABÍ", bold: true, size: 20 })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 300 },
      children: [new TextRun({ text: "ACTA TÉCNICA", bold: true, size: 32 })],
    }),
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      rows: [
        new TableRow({ children: [celdaEtiqueta("N.º Acta:"), celdaValor([datos.numeroActa || "S/N"])] }),
        new TableRow({ children: [celdaEtiqueta("Fecha:"), celdaValor([datos.fechaLarga])] }),
        new TableRow({ children: [celdaEtiqueta("Lugar:"), celdaValor([datos.lugar])] }),
        new TableRow({ children: [celdaEtiqueta("Hora de inicio:"), celdaValor([datos.horaInicio])] }),
        new TableRow({ children: [celdaEtiqueta("Hora de finalización:"), celdaValor([datos.horaFin])] }),
        new TableRow({ children: [celdaEtiqueta("Convocado por:"), celdaValor([datos.convocanteNombre, datos.convocanteCargo])] }),
      ],
    }),
    new Paragraph({ spacing: { before: 300, after: 150 }, children: [new TextRun({ text: "PARTICIPANTES", bold: true, size: 24 })] }),
    ...(datos.participantes.length > 0
      ? datos.participantes.map((p) => new Paragraph(`${p.nombre} — ${p.cargo}`))
      : [new Paragraph("Sin participantes registrados.")]),
    new Paragraph({ spacing: { before: 300, after: 150 }, children: [new TextRun({ text: "DESARROLLO DE LA REUNIÓN", bold: true, size: 24 })] }),
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: SIN_BORDES,
      rows: [
        new TableRow({ children: [new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "Puntos del orden del día:", bold: true })] })] })] }),
        new TableRow({ children: [new TableCell({ children: datos.aspectosIA.split("\n").map((l) => new Paragraph(l)) })] }),
        new TableRow({ children: [new TableCell({ children: datos.desarrolloIA.split("\n").map((l) => new Paragraph(l)) })] }),
      ],
    }),
    new Paragraph({ spacing: { before: 300, after: 150 }, children: [new TextRun({ text: "COMPROMISOS Y ACUERDOS", bold: true, size: 24 })] }),
    ...datos.compromisosIA.split("\n").map((l) => new Paragraph(l)),
  ];

  if (fotos.length > 0) {
    children.push(
      new Paragraph({ children: [new PageBreak()] }),
      new Paragraph({ children: [new TextRun({ text: "EVIDENCIAS FOTOGRÁFICAS", bold: true, size: 24 })] })
    );
    fotos.forEach((foto, i) => {
      children.push(
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new ImageRun({ type: foto.tipo, data: foto.buffer, transformation: { width: 500, height: 350 } })],
        }),
        new Paragraph({ alignment: AlignmentType.CENTER, text: `Figura ${i + 1}` })
      );
    });
  }

  children.push(
    new Paragraph({ spacing: { before: 300, after: 150 }, children: [new TextRun({ text: "FIRMANTES", bold: true, size: 24 })] }),
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      rows: [
        new TableRow({
          children: [
            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "NOMBRE Y CARGO", bold: true })] })] }),
            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "FIRMA", bold: true })] })] }),
          ],
        }),
        ...firmantes.map(
          (f) =>
            new TableRow({
              children: [
                new TableCell({ children: [new Paragraph(f.nombre), new Paragraph(f.cargo)] }),
                new TableCell({ children: [new Paragraph("")] }),
              ],
            })
        ),
      ],
    }),
    new Paragraph({
      spacing: { before: 300 },
      children: [new TextRun(`Elaborado por: ${datos.elaboradoTitulo} ${datos.elaboradoNombre}`)],
    })
  );

  const doc = new Document({ sections: [{ children }] });
  return Packer.toBuffer(doc);
}

export function formatearFechaActa(fecha: string): string {
  return formatearFechaLarga(fecha);
}
