"use client";

import { useEffect, useState } from "react";

interface RubricaResumen { id: number; slug: string; subtipo: string | null }
interface Modalidad { id: number; slug: string; nombre: string; requiere_subtipo: boolean; rubricas: RubricaResumen[] }

interface Criterio { no: number; texto: string; peso: number; descriptores?: Record<string, string>; niveles?: Record<string, string> }
interface Tabla { nombre: string; escala: string; header_rows: number; criterios: Criterio[] }
interface Schema { escala_total: number; tabla_total_idx: number; tablas: Tabla[] }

interface Indicador {
  tabla_idx: number; criterio_idx: number; criterio_texto: string; peso: number;
  respuesta: string | null; calificacion: number | null; comentario: string; sugerencia_ia?: string | null;
}
interface Observacion { id: number; seccion: "formal" | "fondo"; componente: string; observacion: string }

interface Detalle {
  id: number; estudiante: string | null; titulo_trabajo: string | null; texto_trabajo: string | null;
  rubrica: { id: number; slug: string; schema: Schema } | null;
  indicadores: Indicador[]; observaciones: Observacion[]; puntaje_total: number;
}

const NIVELES_PCT = ["0", "35", "70", "100"];

export default function ParesLectoresPage() {
  const [paso, setPaso] = useState(1);
  const [evaluacionId, setEvaluacionId] = useState<number | null>(null);

  // Paso 1: datos del memo
  const [numeroMemo, setNumeroMemo] = useState("");
  const [fechaMemo, setFechaMemo] = useState("");
  const [facultad, setFacultad] = useState("");
  const [carrera, setCarrera] = useState("");
  const [opcionTitulacion, setOpcionTitulacion] = useState("");
  const [tituloTrabajo, setTituloTrabajo] = useState("");
  const [estudiante, setEstudiante] = useState("");
  const [tutor, setTutor] = useState("");
  const [evaluadorNombre, setEvaluadorNombre] = useState("");
  const [evaluadorCorreo, setEvaluadorCorreo] = useState("");
  const [precargando, setPrecargando] = useState(false);
  const [precargaError, setPrecargaError] = useState("");

  // Paso 2: modalidad/rubrica
  const [modalidades, setModalidades] = useState<Modalidad[]>([]);
  const [modalidadId, setModalidadId] = useState<number | null>(null);
  const [rubricaId, setRubricaId] = useState<number | null>(null);

  // Paso 3: archivos
  const [subiendoMemo, setSubiendoMemo] = useState(false);
  const [subiendoTrabajo, setSubiendoTrabajo] = useState(false);
  const [trabajoSubido, setTrabajoSubido] = useState(false);

  // Paso 4: detalle + indicadores + observaciones
  const [detalle, setDetalle] = useState<Detalle | null>(null);
  const [sugiriendoIdx, setSugiriendoIdx] = useState<number | null>(null);

  const [generando, setGenerando] = useState(false);

  useEffect(() => {
    fetch("/herramientas/pares-lectores/api/modalidades").then((r) => r.json()).then(setModalidades);
  }, []);

  async function precargarDesdeMemo(archivo: File) {
    setPrecargando(true);
    setPrecargaError("");
    try {
      const fd = new FormData();
      fd.set("archivo", archivo);
      const r = await fetch("/herramientas/pares-lectores/api/precargar-memo", { method: "POST", body: fd });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error);
      setNumeroMemo(d.numero_memo || "");
      setFechaMemo(d.fecha_memo || "");
      setFacultad(d.facultad || "");
      setCarrera(d.carrera || "");
      setOpcionTitulacion(d.opcion_titulacion || "");
      setTituloTrabajo(d.titulo_trabajo || "");
      setEstudiante(d.estudiante || "");
      setTutor(d.tutor || "");
    } catch (e) {
      setPrecargaError((e as Error).message);
    } finally {
      setPrecargando(false);
    }
  }

  async function crearEvaluacion(e: React.FormEvent) {
    e.preventDefault();
    const r = await fetch("/herramientas/pares-lectores/api/evaluacion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        numero_memo: numeroMemo, fecha_memo: fechaMemo, facultad, carrera,
        opcion_titulacion: opcionTitulacion, titulo_trabajo: tituloTrabajo, estudiante, tutor,
        evaluador_nombre: evaluadorNombre, evaluador_correo: evaluadorCorreo,
      }),
    });
    const d = await r.json();
    if (!r.ok) { alert(d.error); return; }
    setEvaluacionId(d.evaluacion_id);
    setPaso(2);
  }

  const modalidadActual = modalidades.find((m) => m.id === modalidadId);

  async function confirmarModalidad() {
    if (!evaluacionId || !modalidadId || !rubricaId) return;
    const r = await fetch(`/herramientas/pares-lectores/api/evaluacion/${evaluacionId}/modalidad`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ modalidad_id: modalidadId, rubrica_id: rubricaId }),
    });
    if (!r.ok) { alert((await r.json()).error); return; }
    setPaso(3);
  }

  async function subirArchivo(tipo: "memo" | "trabajo", archivo: File) {
    if (!evaluacionId) return;
    const setSubiendo = tipo === "memo" ? setSubiendoMemo : setSubiendoTrabajo;
    setSubiendo(true);
    try {
      const fd = new FormData();
      fd.set("tipo", tipo);
      fd.set("archivo", archivo);
      const r = await fetch(`/herramientas/pares-lectores/api/evaluacion/${evaluacionId}/archivo`, { method: "POST", body: fd });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error);
      if (tipo === "trabajo") setTrabajoSubido(true);
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setSubiendo(false);
    }
  }

  async function irAPaso4() {
    if (!evaluacionId) return;
    const r = await fetch(`/herramientas/pares-lectores/api/evaluacion/${evaluacionId}/detalle`);
    const d = await r.json();
    if (!r.ok) { alert(d.error); return; }
    if (!d.rubrica) { alert("Falta la rúbrica."); return; }

    const criteriosSchema = d.rubrica.schema.tablas[0].criterios;
    const indicadoresExistentes = new Map<number, Indicador>((d.indicadores as Indicador[]).map((i) => [i.criterio_idx, i]));
    d.indicadores = criteriosSchema.map((c: Criterio, idx: number) => indicadoresExistentes.get(idx) ?? {
      tabla_idx: 0, criterio_idx: idx, criterio_texto: c.texto, peso: c.peso,
      respuesta: null, calificacion: null, comentario: "", sugerencia_ia: null,
    });
    setDetalle(d);
    setPaso(4);
  }

  function actualizarIndicador(idx: number, cambios: Partial<Indicador>) {
    if (!detalle) return;
    setDetalle({
      ...detalle,
      indicadores: detalle.indicadores.map((ind, i) => (i === idx ? { ...ind, ...cambios } : ind)),
    });
  }

  function calificacionParaRespuesta(peso: number, respuesta: string | null, escala: string): number | null {
    if (!respuesta) return null;
    if (escala === "peso_si_no" || escala === "si_no") return respuesta === "YES" ? peso : 0;
    const pct = Number(respuesta === "90" ? "90" : respuesta) / 100;
    return Math.round(peso * pct * 100) / 100;
  }

  async function guardarIndicadores() {
    if (!evaluacionId || !detalle) return;
    await fetch(`/herramientas/pares-lectores/api/evaluacion/${evaluacionId}/indicadores`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(detalle.indicadores),
    });
  }

  async function sugerirIA(idx: number) {
    if (!evaluacionId || !detalle) return;
    setSugiriendoIdx(idx);
    try {
      const r = await fetch(`/herramientas/pares-lectores/api/evaluacion/${evaluacionId}/sugerir-indicador`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ criterio_texto: detalle.indicadores[idx].criterio_texto }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error);
      actualizarIndicador(idx, { comentario: d.sugerencia, sugerencia_ia: d.sugerencia });
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setSugiriendoIdx(null);
    }
  }

  function actualizarObservacion(id: number, observacion: string) {
    if (!detalle) return;
    setDetalle({ ...detalle, observaciones: detalle.observaciones.map((o) => (o.id === id ? { ...o, observacion } : o)) });
  }

  async function guardarObservaciones() {
    if (!evaluacionId || !detalle) return;
    await fetch(`/herramientas/pares-lectores/api/evaluacion/${evaluacionId}/observaciones`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(detalle.observaciones),
    });
  }

  async function generarDocumentos() {
    if (!evaluacionId) return;
    setGenerando(true);
    try {
      await guardarIndicadores();
      await guardarObservaciones();
      const r = await fetch(`/herramientas/pares-lectores/api/evaluacion/${evaluacionId}/generar`, { method: "POST" });
      if (!r.ok) throw new Error((await r.json()).error);
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Evaluacion_${evaluacionId}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Error al generar los documentos: ${(e as Error).message}`);
    } finally {
      setGenerando(false);
    }
  }

  const escala = detalle?.rubrica?.schema.tablas[0].escala;
  const puntajeCalculado = detalle
    ? Math.round(
        detalle.indicadores.reduce((acc, ind) => acc + (ind.calificacion ?? 0), 0) * 100
      ) / 100
    : 0;

  return (
    <main className="mx-auto max-w-4xl p-6">
      <h1 className="mb-2 text-2xl font-bold text-[#003366]">📋 Evaluación de Pares Lectores</h1>
      <p className="mb-6 text-sm text-slate-500">Paso {paso} de 4</p>

      {paso === 1 && (
        <form onSubmit={crearEvaluacion} className="space-y-4">
          <fieldset className="rounded-lg border border-slate-300 p-4">
            <legend className="px-2 font-semibold text-[#003366]">Precargar desde el memo (opcional)</legend>
            <input type="file" accept=".pdf,.docx" onChange={(e) => e.target.files?.[0] && precargarDesdeMemo(e.target.files[0])} className="ht-input" />
            {precargando && <p className="mt-2 text-sm text-slate-500">⏳ Extrayendo datos con IA...</p>}
            {precargaError && <p className="mt-2 text-sm text-red-600">❌ {precargaError}</p>}
          </fieldset>

          <fieldset className="rounded-lg border border-slate-300 p-4">
            <legend className="px-2 font-semibold text-[#003366]">Datos del memo</legend>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm">N.º de memo<input value={numeroMemo} onChange={(e) => setNumeroMemo(e.target.value)} className="ht-input" /></label>
              <label className="text-sm">Fecha del memo<input required type="date" value={fechaMemo} onChange={(e) => setFechaMemo(e.target.value)} className="ht-input" /></label>
              <label className="text-sm">Facultad<input value={facultad} onChange={(e) => setFacultad(e.target.value)} className="ht-input" /></label>
              <label className="text-sm">Carrera<input value={carrera} onChange={(e) => setCarrera(e.target.value)} className="ht-input" /></label>
              <label className="text-sm">Opción de titulación<input value={opcionTitulacion} onChange={(e) => setOpcionTitulacion(e.target.value)} className="ht-input" /></label>
              <label className="text-sm">Título del trabajo<input value={tituloTrabajo} onChange={(e) => setTituloTrabajo(e.target.value)} className="ht-input" /></label>
              <label className="text-sm">Estudiante<input value={estudiante} onChange={(e) => setEstudiante(e.target.value)} className="ht-input" /></label>
              <label className="text-sm">Tutor/a<input value={tutor} onChange={(e) => setTutor(e.target.value)} className="ht-input" /></label>
              <label className="text-sm">Su nombre (evaluador/a)<input required value={evaluadorNombre} onChange={(e) => setEvaluadorNombre(e.target.value)} className="ht-input" /></label>
              <label className="text-sm">Su correo institucional<input required type="email" value={evaluadorCorreo} onChange={(e) => setEvaluadorCorreo(e.target.value)} className="ht-input" /></label>
            </div>
          </fieldset>

          <button type="submit" className="ht-btn-primary w-full">Continuar →</button>
        </form>
      )}

      {paso === 2 && (
        <div className="space-y-4">
          <fieldset className="rounded-lg border border-slate-300 p-4">
            <legend className="px-2 font-semibold text-[#003366]">Modalidad y rúbrica</legend>
            <label className="mb-3 block text-sm">
              Modalidad
              <select value={modalidadId ?? ""} onChange={(e) => { setModalidadId(Number(e.target.value)); setRubricaId(null); }} className="ht-input">
                <option value="" disabled>-- Seleccione --</option>
                {modalidades.map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
              </select>
            </label>
            {modalidadActual && modalidadActual.rubricas.length > 1 && (
              <label className="block text-sm">
                Subtipo / rúbrica
                <select value={rubricaId ?? ""} onChange={(e) => setRubricaId(Number(e.target.value))} className="ht-input">
                  <option value="" disabled>-- Seleccione --</option>
                  {modalidadActual.rubricas.map((r) => <option key={r.id} value={r.id}>{r.subtipo || r.slug}</option>)}
                </select>
              </label>
            )}
            {modalidadActual && modalidadActual.rubricas.length === 1 && (
              <p className="text-sm text-slate-500">Rúbrica: {modalidadActual.rubricas[0].slug}</p>
            )}
          </fieldset>
          <button
            onClick={() => {
              if (modalidadActual?.rubricas.length === 1) setRubricaId(modalidadActual.rubricas[0].id);
              confirmarModalidad();
            }}
            disabled={!modalidadId || (!rubricaId && modalidadActual?.rubricas.length !== 1)}
            className="ht-btn-primary w-full disabled:opacity-50"
          >
            Continuar →
          </button>
        </div>
      )}

      {paso === 3 && (
        <div className="space-y-4">
          <fieldset className="rounded-lg border border-slate-300 p-4">
            <legend className="px-2 font-semibold text-[#003366]">Archivos (no se almacenan — solo se extrae el texto)</legend>
            <label className="mb-4 block text-sm">
              Memo (PDF/DOCX, opcional)
              <input type="file" accept=".pdf,.docx,.doc" onChange={(e) => e.target.files?.[0] && subirArchivo("memo", e.target.files[0])} className="ht-input" />
              {subiendoMemo && <span className="text-xs text-slate-500">Procesando...</span>}
            </label>
            <label className="block text-sm">
              Trabajo del estudiante (PDF/DOCX, requerido para sugerencias de IA)
              <input type="file" accept=".pdf,.docx,.doc" onChange={(e) => e.target.files?.[0] && subirArchivo("trabajo", e.target.files[0])} className="ht-input" />
              {subiendoTrabajo && <span className="text-xs text-slate-500">Procesando...</span>}
              {trabajoSubido && <span className="text-xs text-green-600">✅ Texto extraído.</span>}
            </label>
          </fieldset>
          <button onClick={irAPaso4} className="ht-btn-primary w-full">Continuar →</button>
        </div>
      )}

      {paso === 4 && detalle && (
        <div className="space-y-6">
          <fieldset className="rounded-lg border border-slate-300 p-4">
            <legend className="px-2 font-semibold text-[#003366]">Rúbrica interactiva — {detalle.rubrica?.schema.tablas[0].nombre}</legend>
            <div className="space-y-4">
              {detalle.indicadores.map((ind, idx) => (
                <div key={idx} className="rounded-md border border-slate-200 p-3">
                  <p className="mb-2 text-sm font-medium">{ind.criterio_texto} <span className="text-slate-400">(peso {ind.peso})</span></p>
                  {(escala === "peso_si_no" || escala === "si_no") ? (
                    <div className="flex gap-4 text-sm">
                      {["YES", "NO"].map((v) => (
                        <label key={v} className="flex items-center gap-1">
                          <input type="radio" checked={ind.respuesta === v}
                            onChange={() => actualizarIndicador(idx, { respuesta: v, calificacion: calificacionParaRespuesta(ind.peso, v, escala!) })} />
                          {v}
                        </label>
                      ))}
                      <span className="ml-auto text-slate-500">Puntaje: {ind.calificacion ?? "—"}</span>
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-3 text-sm">
                      {NIVELES_PCT.map((pct) => (
                        <label key={pct} className="flex items-center gap-1">
                          <input type="radio" checked={ind.respuesta === pct}
                            onChange={() => actualizarIndicador(idx, { respuesta: pct, calificacion: calificacionParaRespuesta(ind.peso, pct, escala!) })} />
                          {pct}%
                        </label>
                      ))}
                      <span className="ml-auto text-slate-500">Puntaje: {ind.calificacion ?? "—"}</span>
                    </div>
                  )}
                  <div className="mt-2 flex gap-2">
                    <textarea rows={2} value={ind.comentario} onChange={(e) => actualizarIndicador(idx, { comentario: e.target.value })}
                      placeholder="Comentario" className="ht-input flex-1" />
                    <button type="button" onClick={() => sugerirIA(idx)} disabled={sugiriendoIdx === idx || !trabajoSubido}
                      className="shrink-0 rounded bg-green-600 px-3 text-xs font-semibold text-white disabled:opacity-50">
                      {sugiriendoIdx === idx ? "..." : "✨ IA"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-4 text-right font-semibold text-[#003366]">
              Puntaje total: {puntajeCalculado} / {detalle.rubrica?.schema.escala_total}
            </p>
          </fieldset>

          <fieldset className="rounded-lg border border-slate-300 p-4">
            <legend className="px-2 font-semibold text-[#003366]">Observaciones — Aspectos formales</legend>
            {detalle.observaciones.filter((o) => o.seccion === "formal").map((o) => (
              <label key={o.id} className="mb-2 block text-sm">
                {o.componente}
                <input value={o.observacion} onChange={(e) => actualizarObservacion(o.id, e.target.value)} className="ht-input" />
              </label>
            ))}
          </fieldset>
          <fieldset className="rounded-lg border border-slate-300 p-4">
            <legend className="px-2 font-semibold text-[#003366]">Observaciones — Aspectos de fondo</legend>
            {detalle.observaciones.filter((o) => o.seccion === "fondo").map((o) => (
              <label key={o.id} className="mb-2 block text-sm">
                {o.componente}
                <input value={o.observacion} onChange={(e) => actualizarObservacion(o.id, e.target.value)} className="ht-input" />
              </label>
            ))}
          </fieldset>

          <button onClick={generarDocumentos} disabled={generando} className="ht-btn-primary w-full">
            {generando ? "Generando..." : "📦 Generar Informe + Rúbrica (.zip)"}
          </button>
        </div>
      )}
    </main>
  );
}
