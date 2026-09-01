const MESES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

/** Convierte "2026-04-15" en "15 de abril de 2026". Si ya viene en ese formato, la deja igual. */
export function formatearFechaLarga(fechaStr: string | undefined | null): string {
  if (!fechaStr) return "";
  if (fechaStr.includes(" de ")) return fechaStr;
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(fechaStr);
  if (!match) return fechaStr;
  const [, anio, mes, dia] = match;
  const mesIdx = parseInt(mes, 10) - 1;
  if (mesIdx < 0 || mesIdx > 11) return fechaStr;
  return `${parseInt(dia, 10)} de ${MESES[mesIdx]} de ${anio}`;
}

/** dd/mm/yyyy a partir de un Date. */
export function formatearFechaCorta(fecha: Date): string {
  const dia = String(fecha.getDate()).padStart(2, "0");
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  return `${dia}/${mes}/${fecha.getFullYear()}`;
}

/** "15 de abril del 2026" (variante "del", usada en PAT-06). */
export function formatearFechaLargaDel(fecha: Date): string {
  return `${fecha.getDate()} de ${MESES[fecha.getMonth()]} del ${fecha.getFullYear()}`;
}

/** Suma días hábiles (lun-vie) a una fecha, saltando sábados y domingos. */
export function diasHabilesDesde(fechaInicio: Date, dias: number): Date {
  const fecha = new Date(fechaInicio.getTime());
  let restantes = dias;
  while (restantes > 0) {
    fecha.setDate(fecha.getDate() + 1);
    const diaSemana = fecha.getDay(); // 0=domingo .. 6=sábado
    if (diaSemana !== 0 && diaSemana !== 6) restantes -= 1;
  }
  return fecha;
}

/** Plazo de 5 días hábiles desde la fecha del memo (política 6.1.bb Manual de Titulación). */
export function calcularFechaLimite(fechaMemoStr: string): string {
  const fechaMemo = new Date(`${fechaMemoStr}T00:00:00`);
  const fechaLimite = diasHabilesDesde(fechaMemo, 5);
  return fechaLimite.toISOString().slice(0, 10);
}

/** Resta `semanas` semanas a una fecha. */
export function restarSemanas(fecha: Date, semanas: number): Date {
  const resultado = new Date(fecha.getTime());
  resultado.setDate(resultado.getDate() - semanas * 7);
  return resultado;
}

/** "16:00" -> "18:00" (suma horas enteras, con wraparound a 24h). */
export function sumarHoras(horaStr: string | undefined | null, horas: number, fallback = "18:00"): string {
  if (!horaStr) return fallback;
  const match = /^(\d{1,2}):(\d{2})/.exec(horaStr);
  if (!match) return fallback;
  const h = (parseInt(match[1], 10) + horas) % 24;
  return `${String(h).padStart(2, "0")}:${match[2]}`;
}
