import { renderizarPlantilla, fusionarDocx } from "./docxtemplater";
import { formatearFechaCorta, formatearFechaLargaDel, restarSemanas, sumarHoras } from "./fechas";

interface InfoMaestria {
  nombre: string;
  responsable: string;
}

/** Copiado literal de logic/PatsMaestria.py. */
const INFO_MAESTRIAS: Record<string, InfoMaestria> = {
  "1": {
    nombre: "Maestría en Educación con Mención en Lingüística y Literatura, Cohorte IV – Matriz Manta.",
    responsable: "Mg. Vargas Parraga Vanessa Monserrate",
  },
  "2": {
    nombre: "Maestría en Educación con Mención en Innovaciones Pedagógicas, Cohorte IV – sede Matriz.",
    responsable: "Mg. Delgado Mero Diana Maria",
  },
  "3": {
    nombre: "Maestría en Pedagogía de los Idiomas Nacionales y Extranjeros Mención Inglés Matriz Manta, Cohorte III.",
    responsable: "Mg. Bazurto Alcivar Gabriel José",
  },
};

const TEMAS_MAP: Record<string, string[]> = {
  "1": ["Socialización de los PAT (003- 006)", "Selección de revista a publicar", "Delimitación del tema", "Formulación del problema", "Diseño del protocolo", "Búsqueda sistemática", "Análisis y categorización", "Redacción del marco teórico", "Elaboración de discusión"],
  "2": ["Socialización PAT", "Problema de investigación", "Justificación y objetivos", "Marco referencial", "Variables de estudio", "Diseño metodológico", "Población y muestra", "Validación de instrumentos", "Planificación del análisis"],
  "3": ["Socialización PAT", "Planteamiento de hipótesis", "Antecedentes teóricos", "Plan de intervención", "Asignación de grupos", "Pilotaje de instrumentos", "Implementación y recolección", "Aplicación de Pre-test", "Análisis de validación"],
};

export interface DatosPats {
  MAESTRIA: string;
  responsable: string;
  temas: string[];
  nombre: string;
  articulo: string;
  oficio: string;
  fechaFinal: Date;
  fechaDesignacion: string; // dd/mm/yyyy
  hora: string;
}

export function prepararDatosParaPats(form: FormData): DatosPats {
  const maestriaOpcion = (form.get("maestria_opcion")?.toString() ?? "").trim();
  const metodologiaOpcion = (form.get("metodologia_opcion")?.toString() ?? "1").trim();

  const fechaSesionStr = form.get("fecha_sesion")?.toString() ?? "";
  const fechaDesignacionStr = form.get("fecha_designacion")?.toString() ?? "";

  const fechaSesion = fechaSesionStr ? new Date(`${fechaSesionStr}T00:00:00`) : new Date();
  const fechaDesignacion = fechaDesignacionStr
    ? formatearFechaCorta(new Date(`${fechaDesignacionStr}T00:00:00`))
    : formatearFechaCorta(new Date());

  const info = INFO_MAESTRIAS[maestriaOpcion];

  return {
    MAESTRIA: info?.nombre ?? "Maestría no encontrada",
    responsable: info?.responsable ?? "Responsable no encontrado",
    temas: TEMAS_MAP[metodologiaOpcion] ?? TEMAS_MAP["1"],
    nombre: (form.get("nombre_maestrante")?.toString() ?? "").toUpperCase(),
    articulo: form.get("titulo_articulo")?.toString() ?? "",
    oficio: form.get("num_oficio")?.toString() ?? "",
    fechaFinal: fechaSesion,
    fechaDesignacion,
    hora: form.get("hora_inicio")?.toString() || "16:00",
  };
}

function generarPat03(datos: DatosPats): Buffer {
  const ctx: Record<string, unknown> = {
    articulo: datos.articulo,
    nombre: datos.nombre,
    MAESTRIA: datos.MAESTRIA,
  };
  datos.temas.forEach((t, i) => { ctx[`t${i + 1}`] = t; });
  return renderizarPlantilla("PAT-03-G-001-F-003.docx", ctx);
}

function generarPat04(datos: DatosPats): Buffer {
  const horaFin = sumarHoras(datos.hora, 2);
  const fechas = Array.from({ length: 9 }, (_, i) => formatearFechaCorta(restarSemanas(datos.fechaFinal, 8 - i)));

  const buffers: Buffer[] = [];
  for (let i = 0; i < 9; i++) {
    const proxima = i < 8 ? datos.temas[i + 1] : "Revisión integral para entrega final";
    buffers.push(renderizarPlantilla("PAT-03-G-001-F-004.docx", {
      No: i + 1,
      Articulo: datos.articulo,
      NOMBRE: datos.nombre,
      FECHA: fechas[i],
      HORA: datos.hora,
      HoraFin: horaFin,
      Tema: datos.temas[i],
      Proxima: proxima,
    }));
  }
  return fusionarDocx(buffers);
}

function generarPat05(datos: DatosPats): Buffer {
  const fechas = Array.from({ length: 9 }, (_, i) => formatearFechaCorta(restarSemanas(datos.fechaFinal, 8 - i)));
  const horaFin = sumarHoras(datos.hora, 2);

  const ctx: Record<string, unknown> = {
    MAESTRIA: datos.MAESTRIA,
    Articulo: datos.articulo,
    NOMBRE: datos.nombre,
    FECHA: formatearFechaCorta(datos.fechaFinal),
    FechaInicio: fechas[0],
    FechaDesignacion: datos.fechaDesignacion,
    HORA: datos.hora,
    HoraFin: horaFin,
    Responsable: datos.responsable,
  };
  datos.temas.forEach((t, i) => {
    ctx[`n${i + 1}`] = i + 1;
    ctx[`f${i + 1}`] = fechas[i];
    ctx[`t${i + 1}`] = t;
  });
  return renderizarPlantilla("PAT-03-G-001-F-005.docx", ctx);
}

function generarPat06(datos: DatosPats): Buffer {
  const fechaCarta = new Date(datos.fechaFinal.getTime());
  fechaCarta.setDate(fechaCarta.getDate() + 1);

  return renderizarPlantilla("PAT-03-G-001-F-006.docx", {
    FechaCarta: formatearFechaLargaDel(fechaCarta),
    Oficio: datos.oficio,
    NOMBRE: datos.nombre,
    Articulo: datos.articulo,
    TutorFirma: "Dr. Rodríguez Zambrano Arturo Damián, PhD",
  });
}

export function generarDocumentosPats(datos: DatosPats): Array<{ nombre: string; buffer: Buffer }> {
  return [
    { nombre: "PAT_003_Cronograma.docx", buffer: generarPat03(datos) },
    { nombre: "PAT_004_Oficio.docx", buffer: generarPat04(datos) },
    { nombre: "PAT_005_Asistencia.docx", buffer: generarPat05(datos) },
    { nombre: "PAT_006_Informe.docx", buffer: generarPat06(datos) },
  ];
}
