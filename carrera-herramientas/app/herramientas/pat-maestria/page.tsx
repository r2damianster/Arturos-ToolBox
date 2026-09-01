"use client";

import { useState } from "react";

export default function PatMaestriaPage() {
  const [maestriaOpcion, setMaestriaOpcion] = useState("1");
  const [nombreMaestrante, setNombreMaestrante] = useState("");
  const [tituloArticulo, setTituloArticulo] = useState("");
  const [metodologiaOpcion, setMetodologiaOpcion] = useState("1");
  const [numOficio, setNumOficio] = useState("");
  const [horaInicio, setHoraInicio] = useState("16:00");
  const [fechaSesion, setFechaSesion] = useState("");
  const [fechaDesignacion, setFechaDesignacion] = useState("");
  const [generando, setGenerando] = useState(false);

  async function generar(e: React.FormEvent) {
    e.preventDefault();
    setGenerando(true);
    try {
      const fd = new FormData();
      fd.set("maestria_opcion", maestriaOpcion);
      fd.set("nombre_maestrante", nombreMaestrante);
      fd.set("titulo_articulo", tituloArticulo);
      fd.set("metodologia_opcion", metodologiaOpcion);
      fd.set("num_oficio", numOficio);
      fd.set("hora_inicio", horaInicio);
      fd.set("fecha_sesion", fechaSesion);
      fd.set("fecha_designacion", fechaDesignacion);

      const r = await fetch("/herramientas/pat-maestria/api", { method: "POST", body: fd });
      if (!r.ok) throw new Error((await r.json().catch(() => ({ error: "Error desconocido" }))).error);
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `PATS_${(nombreMaestrante || "maestrante").replace(/\s+/g, "_").slice(0, 15)}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Error al generar el paquete PAT: ${(e as Error).message}`);
    } finally {
      setGenerando(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-[#003366]">📦 Documentos PAT de Maestría</h1>
      <form onSubmit={generar} className="space-y-6">
        <fieldset className="rounded-lg border border-slate-300 p-4">
          <legend className="px-2 font-semibold text-[#003366]">Programa y Maestrante</legend>
          <label className="mb-3 block text-sm">
            Maestría
            <select required value={maestriaOpcion} onChange={(e) => setMaestriaOpcion(e.target.value)} className="ht-input">
              <option value="1">Lingüística y Literatura</option>
              <option value="2">Innovaciones Pedagógicas</option>
              <option value="3">Pedagogía de Idiomas (Inglés)</option>
            </select>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm">Nombre del maestrante
              <input required value={nombreMaestrante} onChange={(e) => setNombreMaestrante(e.target.value)}
                placeholder="Nombres y apellidos completos" className="ht-input" />
            </label>
            <label className="text-sm">Título del trabajo/artículo
              <input required value={tituloArticulo} onChange={(e) => setTituloArticulo(e.target.value)} className="ht-input" />
            </label>
          </div>
        </fieldset>

        <fieldset className="rounded-lg border border-slate-300 p-4">
          <legend className="px-2 font-semibold text-[#003366]">Metodología</legend>
          <label className="block text-sm">
            Tipo de investigación (define los temas de sesión)
            <select required value={metodologiaOpcion} onChange={(e) => setMetodologiaOpcion(e.target.value)} className="ht-input">
              <option value="1">Revisión Sistemática</option>
              <option value="2">No Experimental</option>
              <option value="3">Cuasi-Experimental</option>
            </select>
          </label>
        </fieldset>

        <fieldset className="rounded-lg border border-slate-300 p-4">
          <legend className="px-2 font-semibold text-[#003366]">Logística y fechas</legend>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm">N.º Oficio recibido<input required value={numOficio} onChange={(e) => setNumOficio(e.target.value)} className="ht-input" /></label>
            <label className="text-sm">Hora de inicio de sesión<input required type="time" value={horaInicio} onChange={(e) => setHoraInicio(e.target.value)} className="ht-input" /></label>
            <label className="text-sm">Fecha sesión 9 (última)<input required type="date" value={fechaSesion} onChange={(e) => setFechaSesion(e.target.value)} className="ht-input" /></label>
            <label className="text-sm">Fecha designación del tutor<input required type="date" value={fechaDesignacion} onChange={(e) => setFechaDesignacion(e.target.value)} className="ht-input" /></label>
          </div>
        </fieldset>

        <button type="submit" disabled={generando} className="ht-btn-primary w-full">
          {generando ? "Generando..." : "📦 Generar Paquete PAT (.zip)"}
        </button>
      </form>
    </main>
  );
}
