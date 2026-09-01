"use client";

import { useEffect, useMemo, useState } from "react";

interface Docente {
  id: number;
  titulo_grado: string;
  nombre: string;
  post_grado: string;
  cargo: string;
  carrera: string;
}

interface DocenteManual {
  titulo: string;
  nombre: string;
  postgrado: string;
  cargo: string;
}

const PERIODOS = ["2026-1", "2026-2"];
const CURSOS_DISPONIBLES = [
  "Primer Semestre 'A'", "Segundo Semestre 'A'", "Tercer Semestre 'A'",
  "Cuarto Semestre 'A'", "Cuarto Semestre 'B'", "Quinto Semestre 'A'", "Sexto Semestre 'A'",
];

async function enriquecer(contexto: string, texto: string): Promise<string> {
  const r = await fetch("/herramientas/api/ia-enriquecer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contexto, texto }),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || "Error de IA");
  return d.texto_enriquecido;
}

function descargarBlob(blob: Blob, nombreArchivo: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombreArchivo;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ConvocatoriasPage() {
  const [tab, setTab] = useState<"docente" | "estudiante">("docente");
  const [docentes, setDocentes] = useState<Docente[]>([]);

  useEffect(() => {
    fetch("/herramientas/api/docentes").then((r) => r.json()).then(setDocentes);
  }, []);

  const carreras = useMemo(() => Array.from(new Set(docentes.map((d) => d.carrera))), [docentes]);

  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-[#003366]">📢 Convocatorias</h1>
      <div className="mb-6 flex gap-2">
        <button onClick={() => setTab("docente")}
          className={`rounded-t-lg px-4 py-2 text-sm font-semibold ${tab === "docente" ? "bg-[#003366] text-white" : "bg-slate-100 text-slate-600"}`}>
          👨‍🏫 A Docentes
        </button>
        <button onClick={() => setTab("estudiante")}
          className={`rounded-t-lg px-4 py-2 text-sm font-semibold ${tab === "estudiante" ? "bg-[#003366] text-white" : "bg-slate-100 text-slate-600"}`}>
          🎓 A Estudiantes
        </button>
      </div>
      {tab === "docente"
        ? <FormDocentes docentes={docentes} carreras={carreras} />
        : <FormEstudiantes />}
    </main>
  );
}

function FormDocentes({ docentes, carreras }: { docentes: Docente[]; carreras: string[] }) {
  const [numConvocatoria, setNumConvocatoria] = useState("");
  const [periodo, setPeriodo] = useState("");
  const [ciudad, setCiudad] = useState("Manta");
  const [fecha, setFecha] = useState("");

  const [asunto, setAsunto] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [iaStatus, setIaStatus] = useState<{ texto: string; color: string } | null>(null);

  const [fechaReunion, setFechaReunion] = useState("");
  const [horaReunion, setHoraReunion] = useState("");
  const [lugarReunion, setLugarReunion] = useState("");

  const [modo, setModo] = useState<"carrera" | "manual">("carrera");
  const [carreraSeleccionada, setCarreraSeleccionada] = useState("");
  const [manuales, setManuales] = useState<DocenteManual[]>([]);
  const [manualTitulo, setManualTitulo] = useState("Lic.");
  const [manualNombre, setManualNombre] = useState("");
  const [manualPostgrado, setManualPostgrado] = useState("Mg.");
  const [manualCargo, setManualCargo] = useState("Docente");

  const [convocanteId, setConvocanteId] = useState("");
  const [convocanteTitulo, setConvocanteTitulo] = useState("");
  const [convocanteNombre, setConvocanteNombre] = useState("");
  const [convocanteCargo, setConvocanteCargo] = useState("");
  const [inicialesElaborador, setInicialesElaborador] = useState("");
  const [generando, setGenerando] = useState(false);

  const docentesCarrera = docentes.filter((d) => d.carrera === carreraSeleccionada);
  const opcionesConvocante = modo === "carrera"
    ? docentesCarrera.map((d) => ({ id: String(d.id), titulo: d.titulo_grado, nombre: d.nombre, postgrado: d.post_grado, cargo: d.cargo }))
    : manuales.map((d, i) => ({ id: `manual_${i}`, titulo: d.titulo, nombre: d.nombre, postgrado: d.postgrado, cargo: d.cargo }));

  function seleccionarConvocante(id: string) {
    setConvocanteId(id);
    const opcion = opcionesConvocante.find((o) => o.id === id);
    if (!opcion) return;
    setConvocanteTitulo(opcion.titulo);
    setConvocanteNombre(opcion.nombre);
    setConvocanteCargo(opcion.cargo);
  }

  function agregarManual() {
    if (!manualNombre.trim()) { alert("El nombre es obligatorio"); return; }
    setManuales((prev) => [...prev, { titulo: manualTitulo, nombre: manualNombre, postgrado: manualPostgrado, cargo: manualCargo }]);
    setManualNombre("");
  }

  async function mejorarConIA() {
    if (!asunto && !descripcion) {
      setIaStatus({ texto: "⚠️ Escribe algo primero.", color: "text-red-600" });
      return;
    }
    setIaStatus({ texto: "⏳ Procesando...", color: "text-slate-500" });
    try {
      if (asunto.trim().length >= 3) setAsunto(await enriquecer("convocatoria_asunto", asunto));
      if (descripcion.trim().length >= 3) {
        setDescripcion(await enriquecer("convocatoria_descripcion", descripcion));
      } else if (asunto.trim().length >= 3) {
        setDescripcion(await enriquecer("convocatoria_descripcion_generar", asunto));
      }
      setIaStatus({ texto: "✅ Enriquecido. Puedes editar.", color: "text-green-600" });
    } catch (e) {
      setIaStatus({ texto: `❌ ${(e as Error).message}`, color: "text-red-600" });
    }
  }

  async function generar(e: React.FormEvent) {
    e.preventDefault();
    if (modo === "manual" && manuales.length === 0) {
      alert("Agregue al menos un docente");
      return;
    }
    setGenerando(true);
    try {
      const fd = new FormData();
      fd.set("num_convocatoria", numConvocatoria);
      fd.set("periodo", periodo);
      fd.set("ciudad", ciudad);
      fd.set("fecha_larga", fecha);
      fd.set("asunto", asunto);
      fd.set("descripcion_convocatoria", descripcion);
      fd.set("fecha_reunion", fechaReunion);
      fd.set("hora_reunion", horaReunion);
      fd.set("lugar_reunion", lugarReunion);
      fd.set("convocante_titulo", convocanteTitulo);
      fd.set("convocante_nombre", convocanteNombre);
      fd.set("convocante_cargo", convocanteCargo);
      fd.set("iniciales_elaborador", inicialesElaborador);
      fd.set("modo_docentes", modo);
      if (modo === "manual") fd.set("docentes_json", JSON.stringify(manuales));

      const r = await fetch("/herramientas/convocatorias/api/docente", { method: "POST", body: fd });
      if (!r.ok) throw new Error((await r.json().catch(() => ({ error: "Error desconocido" }))).error);
      descargarBlob(await r.blob(), "Convocatoria_Docentes.docx");
    } catch (e) {
      alert(`Error al generar la convocatoria: ${(e as Error).message}`);
    } finally {
      setGenerando(false);
    }
  }

  return (
    <form onSubmit={generar} className="space-y-6">
      <fieldset className="rounded-lg border border-slate-300 p-4">
        <legend className="px-2 font-semibold text-[#003366]">Identificación</legend>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm">N.º Convocatoria<input required value={numConvocatoria} onChange={(e) => setNumConvocatoria(e.target.value)} placeholder="Ej: 001" className="ht-input" /></label>
          <label className="text-sm">Periodo
            <select required value={periodo} onChange={(e) => setPeriodo(e.target.value)} className="ht-input">
              <option value="" disabled>Seleccione...</option>
              {PERIODOS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </label>
          <label className="text-sm">Ciudad<input required value={ciudad} onChange={(e) => setCiudad(e.target.value)} className="ht-input" /></label>
          <label className="text-sm">Fecha de emisión<input required type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} className="ht-input" /></label>
        </div>
      </fieldset>

      <fieldset className="rounded-lg border border-slate-300 p-4">
        <legend className="px-2 font-semibold text-[#003366]">Datos de la reunión</legend>
        <label className="mb-3 block text-sm">Asunto<input required value={asunto} onChange={(e) => setAsunto(e.target.value)} className="ht-input" /></label>
        <label className="block text-sm">Descripción<textarea required rows={3} value={descripcion} onChange={(e) => setDescripcion(e.target.value)} className="ht-input" /></label>
        <div className="mt-3 flex items-center gap-3 rounded-lg border border-green-300 bg-green-50 p-3">
          <button type="button" onClick={mejorarConIA} className="rounded bg-green-600 px-4 py-1.5 text-sm font-semibold text-white">✨ Mejorar con IA</button>
          {iaStatus && <span className={`text-sm ${iaStatus.color}`}>{iaStatus.texto}</span>}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <label className="text-sm">Fecha del evento<input required type="date" value={fechaReunion} onChange={(e) => setFechaReunion(e.target.value)} className="ht-input" /></label>
          <label className="text-sm">Hora<input required type="time" value={horaReunion} onChange={(e) => setHoraReunion(e.target.value)} className="ht-input" /></label>
          <label className="col-span-2 text-sm">Lugar<input required value={lugarReunion} onChange={(e) => setLugarReunion(e.target.value)} className="ht-input" /></label>
        </div>
      </fieldset>

      <fieldset className="rounded-lg border border-slate-300 p-4">
        <legend className="px-2 font-semibold text-[#003366]">Docentes participantes</legend>
        <div className="mb-4 flex gap-6 text-sm font-semibold">
          <label className="flex items-center gap-2"><input type="radio" checked={modo === "carrera"} onChange={() => setModo("carrera")} /> 📋 Docentes de la carrera</label>
          <label className="flex items-center gap-2"><input type="radio" checked={modo === "manual"} onChange={() => setModo("manual")} /> ✏️ Ingresar manualmente</label>
        </div>

        {modo === "carrera" ? (
          <label className="block text-sm">Carrera
            <select value={carreraSeleccionada} onChange={(e) => setCarreraSeleccionada(e.target.value)} className="ht-input">
              <option value="" disabled>-- Seleccione carrera --</option>
              {carreras.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            {carreraSeleccionada && <p className="mt-2 text-xs text-slate-500">{docentesCarrera.length} docentes en esta carrera</p>}
          </label>
        ) : (
          <div>
            <div className="mb-3 grid grid-cols-3 gap-2">
              <input value={manualTitulo} onChange={(e) => setManualTitulo(e.target.value)} placeholder="Título (Lic., Dr.)" className="ht-input" />
              <input value={manualNombre} onChange={(e) => setManualNombre(e.target.value)} placeholder="Nombre completo" className="ht-input" />
              <input value={manualPostgrado} onChange={(e) => setManualPostgrado(e.target.value)} placeholder="Post-grado (Mg., PhD.)" className="ht-input" />
            </div>
            <div className="mb-3 grid grid-cols-[2fr_1fr] gap-2">
              <input value={manualCargo} onChange={(e) => setManualCargo(e.target.value)} placeholder="Cargo" className="ht-input" />
              <button type="button" onClick={agregarManual} className="rounded bg-blue-600 px-4 text-sm font-semibold text-white">➕ Agregar</button>
            </div>
            {manuales.length > 0 && (
              <table className="w-full border-collapse text-sm">
                <thead><tr className="bg-slate-100"><th className="p-1.5 text-left">#</th><th className="p-1.5 text-left">Nombre</th><th className="p-1.5 text-left">Cargo</th><th className="p-1.5">Acción</th></tr></thead>
                <tbody>
                  {manuales.map((d, i) => (
                    <tr key={i} className="border-b border-slate-100">
                      <td className="p-1.5">{i + 1}</td>
                      <td className="p-1.5">{d.titulo} {d.nombre}, {d.postgrado}</td>
                      <td className="p-1.5">{d.cargo}</td>
                      <td className="p-1.5 text-center">
                        <button type="button" onClick={() => setManuales((prev) => prev.filter((_, idx) => idx !== i))} className="rounded bg-red-500 px-2 text-white">✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </fieldset>

      <fieldset className="rounded-lg border border-slate-300 p-4">
        <legend className="px-2 font-semibold text-[#003366]">Firma del convocante</legend>
        <label className="mb-3 block text-sm">Seleccione el convocante
          <select required value={convocanteId} onChange={(e) => seleccionarConvocante(e.target.value)} className="ht-input">
            <option value="" disabled>-- Seleccione un docente --</option>
            {opcionesConvocante.map((o) => <option key={o.id} value={o.id}>{o.titulo} {o.nombre}, {o.postgrado} — {o.cargo}</option>)}
          </select>
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm">Título<input required readOnly value={convocanteTitulo} className="ht-input" /></label>
          <label className="text-sm">Nombre completo<input required readOnly value={convocanteNombre} className="ht-input" /></label>
          <label className="text-sm">Cargo<input required readOnly value={convocanteCargo} className="ht-input" /></label>
          <label className="text-sm">Iniciales elaborador<input required value={inicialesElaborador} onChange={(e) => setInicialesElaborador(e.target.value)} placeholder="Ej: VVP/ddm" className="ht-input" /></label>
        </div>
      </fieldset>

      <button type="submit" disabled={generando} className="ht-btn-primary w-full">
        {generando ? "Generando..." : "📄 Generar Convocatoria Docentes"}
      </button>
    </form>
  );
}

function FormEstudiantes() {
  const [numConvocatoria, setNumConvocatoria] = useState("");
  const [periodo, setPeriodo] = useState("");
  const [ciudad, setCiudad] = useState("Manta");
  const [fecha, setFecha] = useState("");

  const [asunto, setAsunto] = useState("");
  const [cursos, setCursos] = useState<string[]>([]);
  const [descripcion, setDescripcion] = useState("");
  const [iaStatus, setIaStatus] = useState<{ texto: string; color: string } | null>(null);

  const [fechaReunion, setFechaReunion] = useState("");
  const [horaReunion, setHoraReunion] = useState("");
  const [lugarReunion, setLugarReunion] = useState("");

  const [archivos, setArchivos] = useState<File[]>([]);

  const [convocanteTitulo, setConvocanteTitulo] = useState("");
  const [convocanteNombre, setConvocanteNombre] = useState("");
  const [convocanteCargo, setConvocanteCargo] = useState("");
  const [inicialesElaborador, setInicialesElaborador] = useState("");
  const [generando, setGenerando] = useState(false);

  async function mejorarConIA() {
    if (!asunto && !descripcion) {
      setIaStatus({ texto: "⚠️ Escribe algo primero.", color: "text-red-600" });
      return;
    }
    setIaStatus({ texto: "⏳ Procesando...", color: "text-slate-500" });
    try {
      if (asunto.trim().length >= 3) setAsunto(await enriquecer("convocatoria_asunto", asunto));
      if (descripcion.trim().length >= 3) {
        setDescripcion(await enriquecer("convocatoria_descripcion", descripcion));
      } else if (asunto.trim().length >= 3) {
        setDescripcion(await enriquecer("convocatoria_descripcion_generar", asunto));
      }
      setIaStatus({ texto: "✅ Enriquecido. Puedes editar.", color: "text-green-600" });
    } catch (e) {
      setIaStatus({ texto: `❌ ${(e as Error).message}`, color: "text-red-600" });
    }
  }

  async function generar(e: React.FormEvent) {
    e.preventDefault();
    if (archivos.length === 0) {
      alert("Suba al menos un archivo Excel con la lista de estudiantes.");
      return;
    }
    setGenerando(true);
    try {
      const fd = new FormData();
      fd.set("num_convocatoria", numConvocatoria);
      fd.set("periodo", periodo);
      fd.set("ciudad", ciudad);
      fd.set("fecha_larga", fecha);
      fd.set("asunto", asunto);
      cursos.forEach((c) => fd.append("cursos", c));
      fd.set("descripcion_convocatoria", descripcion);
      fd.set("fecha_reunion", fechaReunion);
      fd.set("hora_reunion", horaReunion);
      fd.set("lugar_reunion", lugarReunion);
      fd.set("convocante_titulo", convocanteTitulo);
      fd.set("convocante_nombre", convocanteNombre);
      fd.set("convocante_cargo", convocanteCargo);
      fd.set("iniciales_elaborador", inicialesElaborador);
      archivos.forEach((a) => fd.append("excel_files", a));

      const r = await fetch("/herramientas/convocatorias/api/estudiante", { method: "POST", body: fd });
      if (!r.ok) throw new Error((await r.json().catch(() => ({ error: "Error desconocido" }))).error);
      descargarBlob(await r.blob(), "Convocatoria_Estudiantes.docx");
    } catch (e) {
      alert(`Error al generar la convocatoria: ${(e as Error).message}`);
    } finally {
      setGenerando(false);
    }
  }

  return (
    <form onSubmit={generar} className="space-y-6">
      <fieldset className="rounded-lg border border-slate-300 p-4">
        <legend className="px-2 font-semibold text-[#003366]">Identificación</legend>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm">N.º Convocatoria<input required value={numConvocatoria} onChange={(e) => setNumConvocatoria(e.target.value)} placeholder="Ej: 001" className="ht-input" /></label>
          <label className="text-sm">Periodo académico
            <select required value={periodo} onChange={(e) => setPeriodo(e.target.value)} className="ht-input">
              <option value="" disabled>Seleccione...</option>
              {PERIODOS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </label>
          <label className="text-sm">Ciudad<input required value={ciudad} onChange={(e) => setCiudad(e.target.value)} className="ht-input" /></label>
          <label className="text-sm">Fecha de emisión<input required type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} className="ht-input" /></label>
        </div>
      </fieldset>

      <fieldset className="rounded-lg border border-slate-300 p-4">
        <legend className="px-2 font-semibold text-[#003366]">Datos del evento</legend>
        <label className="mb-3 block text-sm">Asunto<input required value={asunto} onChange={(e) => setAsunto(e.target.value)} className="ht-input" /></label>
        <label className="mb-3 block text-sm">Cursos/Niveles (Ctrl+Clic para varios)
          <select multiple required value={cursos}
            onChange={(e) => setCursos(Array.from(e.target.selectedOptions, (o) => o.value))}
            className="ht-input h-32">
            {CURSOS_DISPONIBLES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className="block text-sm">Descripción del motivo<textarea required rows={3} value={descripcion} onChange={(e) => setDescripcion(e.target.value)} className="ht-input" /></label>
        <div className="mt-3 flex items-center gap-3 rounded-lg border border-green-300 bg-green-50 p-3">
          <button type="button" onClick={mejorarConIA} className="rounded bg-green-600 px-4 py-1.5 text-sm font-semibold text-white">✨ Mejorar con IA</button>
          {iaStatus && <span className={`text-sm ${iaStatus.color}`}>{iaStatus.texto}</span>}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <label className="text-sm">Fecha de reunión<input required type="date" value={fechaReunion} onChange={(e) => setFechaReunion(e.target.value)} className="ht-input" /></label>
          <label className="text-sm">Hora<input required type="time" value={horaReunion} onChange={(e) => setHoraReunion(e.target.value)} className="ht-input" /></label>
          <label className="col-span-2 text-sm">Lugar<input required value={lugarReunion} onChange={(e) => setLugarReunion(e.target.value)} className="ht-input" /></label>
        </div>
      </fieldset>

      <fieldset className="rounded-lg border border-slate-300 p-4">
        <legend className="px-2 font-semibold text-[#003366]">Archivos Excel (uno por curso)</legend>
        <input type="file" accept=".xls,.xlsx,.ods" multiple required
          onChange={(e) => setArchivos(Array.from(e.target.files ?? []))} className="ht-input" />
        <div className="mt-3 rounded-md border border-dashed border-slate-300 p-3 text-sm">
          {archivos.length === 0 ? <em>Ningún archivo seleccionado.</em> : archivos.map((f) => <div key={f.name}>{f.name}</div>)}
        </div>
      </fieldset>

      <fieldset className="rounded-lg border border-slate-300 p-4">
        <legend className="px-2 font-semibold text-[#003366]">Firma</legend>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm">Título<input required value={convocanteTitulo} onChange={(e) => setConvocanteTitulo(e.target.value)} placeholder="Ej: Mg." className="ht-input" /></label>
          <label className="text-sm">Nombre completo<input required value={convocanteNombre} onChange={(e) => setConvocanteNombre(e.target.value)} className="ht-input" /></label>
          <label className="text-sm">Cargo<input required value={convocanteCargo} onChange={(e) => setConvocanteCargo(e.target.value)} className="ht-input" /></label>
          <label className="text-sm">Iniciales elaborador<input required value={inicialesElaborador} onChange={(e) => setInicialesElaborador(e.target.value)} placeholder="Ej: VVP/ddm" className="ht-input" /></label>
        </div>
      </fieldset>

      <button type="submit" disabled={generando} className="ht-btn-primary w-full">
        {generando ? "Generando..." : "📄 Generar Convocatoria Estudiantes"}
      </button>
    </form>
  );
}
