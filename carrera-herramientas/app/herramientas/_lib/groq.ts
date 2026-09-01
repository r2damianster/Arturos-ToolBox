const GROQ_URL = "https://api.groq.com/openai/v1/chat/completions";
const MODELO = "openai/gpt-oss-120b";

export interface MensajeChat {
  role: "system" | "user";
  content: string;
}

interface OpcionesCompletion {
  temperature?: number;
  reasoningEffort?: "low" | "medium" | "high";
  responseFormatJson?: boolean;
}

/** Formatea errores de la API de Groq en un mensaje legible para el usuario final. */
export function formatearErrorIA(error: unknown): string {
  const mensaje = error instanceof Error ? error.message : String(error);
  if (mensaje.includes("429") || mensaje.toLowerCase().includes("rate limit")) {
    return "La IA alcanzó su cuota de uso por ahora. Completa el campo manualmente o intenta en unos minutos.";
  }
  return `No se pudo generar el texto con IA (${mensaje}). Puedes completarlo manualmente.`;
}

/** Llama al chat completion de Groq. Lanza si GROQ_API_KEY no está configurada. */
export async function pedirCompletionIA(mensajes: MensajeChat[], opciones: OpcionesCompletion = {}): Promise<string> {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    throw new Error("IA no configurada (GROQ_API_KEY no definida)");
  }

  const body: Record<string, unknown> = {
    model: MODELO,
    messages: mensajes,
    temperature: opciones.temperature ?? 0.3,
    reasoning_effort: opciones.reasoningEffort ?? "low",
  };
  if (opciones.responseFormatJson) {
    body.response_format = { type: "json_object" };
  }

  const respuesta = await fetch(GROQ_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!respuesta.ok) {
    const detalle = await respuesta.text().catch(() => "");
    throw new Error(`${respuesta.status} ${detalle}`.trim());
  }

  const json = await respuesta.json();
  const contenido = json?.choices?.[0]?.message?.content;
  if (typeof contenido !== "string") {
    throw new Error("Respuesta de la IA sin contenido");
  }
  return contenido.trim();
}
