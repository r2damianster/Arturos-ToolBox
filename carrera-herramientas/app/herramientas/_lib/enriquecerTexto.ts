import { pedirCompletionIA, formatearErrorIA } from "./groq";

interface PromptConfig {
  role: string;
  instruction: string;
  temperature: number;
}

/** Prompts por contexto — copiado de logic/ia_enriquecer.py:PROMPTS. */
export const PROMPTS: Record<string, PromptConfig> = {
  acta_aspectos: {
    role: "Eres un Secretario Académico universitario.",
    instruction:
      "TAREA: Organiza los puntos del orden del día para un acta técnica universitaria.\n" +
      "REGLAS: Sé breve. Corrige ortografía y formaliza el vocabulario. No agregues contenido inventado.\n" +
      "FORMATO: Lista con viñetas (•). Máximo 200 palabras.",
    temperature: 0.2,
  },
  acta_desarrollo: {
    role: "Eres un Secretario Académico universitario.",
    instruction:
      "TAREA: Redacta el desarrollo de una reunión académica a partir de notas breves.\n" +
      "REGLAS: Conecta las ideas con conectores lógicos. Usa tono formal y solemne. " +
      "No inventes hechos, solo expande y mejora la redacción.\n" +
      "FORMATO: 2-3 párrafos narrativos. Máximo 400 palabras.",
    temperature: 0.4,
  },
  acta_compromisos: {
    role: "Eres un Secretario Académico universitario.",
    instruction:
      "TAREA: Redacta acuerdos y compromisos institucionales.\n" +
      "REGLAS: Sé directo. Mantén la esencia sin añadir relleno. Corrige coherencia y ortografía.\n" +
      "FORMATO: Lista con viñetas (•). Máximo 200 palabras.",
    temperature: 0.2,
  },
  convocatoria_asunto: {
    role: "Eres un asistente de redacción administrativa universitaria.",
    instruction:
      "TAREA: Mejora el asunto de una convocatoria académica.\n" +
      "REGLAS: Hazlo claro, formal y conciso. No cambies el significado original.\n" +
      "FORMATO: Una sola línea. Máximo 120 caracteres.",
    temperature: 0.3,
  },
  convocatoria_descripcion: {
    role: "Eres un asistente de redacción administrativa universitaria.",
    instruction:
      "TAREA: Mejora la descripción/motivo de una convocatoria.\n" +
      "REGLAS: Formaliza el lenguaje, mejora la coherencia, sé preciso. No inventes información.\n" +
      "FORMATO: 1-2 párrafos breves. Máximo 250 palabras.",
    temperature: 0.3,
  },
  convocatoria_descripcion_generar: {
    role: "Eres un asistente de redacción administrativa universitaria.",
    instruction:
      "TAREA: Genera el motivo/descripción de una convocatoria universitaria a partir del asunto dado.\n" +
      "REGLAS: Usa lenguaje formal e institucional. Expande el asunto en una descripción clara del " +
      "propósito de la convocatoria. No inventes fechas, nombres ni datos específicos.\n" +
      "FORMATO: 1-2 párrafos. Máximo 200 palabras.",
    temperature: 0.5,
  },
  oficio_asunto: {
    role: "Eres un asistente de redacción administrativa universitaria.",
    instruction:
      "TAREA: Mejora el asunto de un oficio universitario.\n" +
      "REGLAS: Hazlo claro, formal y conciso. No cambies el significado original.\n" +
      "FORMATO: Una sola línea. Máximo 120 caracteres.",
    temperature: 0.3,
  },
  oficio_cuerpo: {
    role: "Eres un asistente de redacción administrativa universitaria.",
    instruction:
      "TAREA: Redacta o mejora el cuerpo de un oficio universitario.\n" +
      "REGLAS: Formaliza el lenguaje, mejora la coherencia, sé preciso. No inventes información. " +
      "Usa estructura: saludo institucional → exposición → solicitud/despedida formal.\n" +
      "FORMATO: 2-4 párrafos. Máximo 350 palabras.",
    temperature: 0.4,
  },
  oficio_cuerpo_generar: {
    role: "Eres un asistente de redacción administrativa universitaria.",
    instruction:
      "TAREA: Genera el cuerpo de un oficio universitario a partir del asunto dado.\n" +
      "REGLAS: Usa estructura formal: saludo institucional → exposición del motivo → " +
      "solicitud o comunicación → despedida formal. No inventes nombres ni datos que no estén en el asunto.\n" +
      "FORMATO: 2-3 párrafos. Máximo 300 palabras.",
    temperature: 0.5,
  },
};

const TONO_INSTRUCCIONES: Record<string, string> = {
  formal: "TONO: Usa lenguaje institucional elevado. Incluye fórmulas de cortesía académica. Mantén distancia protocolar.",
  cordial: "TONO: Usa lenguaje respetuoso pero cálido. Incluye expresiones de colaboración y trabajo en equipo.",
  directo: "TONO: Ve al grano. Usa oraciones cortas. Elimina preámbulos innecesarios. Mantén formalidad básica.",
  urgente: "TONO: Destaca la prioridad y los plazos. Transmite sentido de inmediatez y urgencia.",
};

const CONTEXTOS_CON_TONO = new Set(["oficio_cuerpo", "oficio_cuerpo_generar"]);

/** Enriquece/genera texto con IA según un contexto predefinido. Devuelve [resultado, error]. */
export async function enriquecerTexto(
  contexto: string,
  textoUsuario: string,
  tono?: string
): Promise<[string, null] | [null, string]> {
  if (!textoUsuario || textoUsuario.trim().length < 3) {
    return [null, "El texto es muy corto para enriquecer."];
  }
  const config = PROMPTS[contexto];
  if (!config) {
    return [null, `Contexto no reconocido: ${contexto}`];
  }

  let instruction = config.instruction;
  if (tono && CONTEXTOS_CON_TONO.has(contexto)) {
    const extra = TONO_INSTRUCCIONES[tono];
    if (extra) instruction += `\n${extra}`;
  }

  try {
    const resultado = await pedirCompletionIA(
      [
        { role: "system", content: config.role },
        { role: "user", content: `${instruction}\n\nTEXTO DEL USUARIO:\n${textoUsuario}` },
      ],
      { temperature: config.temperature, reasoningEffort: "low" }
    );
    return [resultado, null];
  } catch (e) {
    return [null, formatearErrorIA(e)];
  }
}
