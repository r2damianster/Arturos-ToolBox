"use client";

import { useEffect, useState } from "react";

interface Docente {
  id: number;
  titulo_grado: string;
  nombre: string;
  post_grado: string;
  cargo: string;
  carrera: string;
}

const TONOS = [
  { value: "formal", label: "🎩 Formal" },
  { value: "cordial", label: "🤝 Cordial" },
  { value: "directo", label: "🎯 Directo" },
  { value: "urgente", label: "⚡ Urgente" },
];

async function enriquecer(contexto: string, texto: string, tono?: string): Promise<string> {
  const r = await fetch("/herramientas/api/ia-enriquecer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contexto, texto, tono }),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || "Error de IA");
  return d.texto_enriquecido;
}

export default function OficiosPage() {
  const [carreras, setCarreras] = useState<string[]>([]);
  const [docentes, setDocentes] = useState<Docente[]>([]);
  const [carreraFiltro, setCarreraFiltro] = useState("");

  const [numOficio, setNumOficio] = useState("");
  const [ciudad, setCiudad] = useState("Manta");
  const [fecha, setFecha] = useState("");
  const [tono, setTono] = useState("formal");

  const [destinatarioNombre, setDestinatarioNombre] = useState("");
  const [destinatarioCargo, setDestinatarioCargo] = useState("");
  const [destinatarioCarrera, setDestinatarioCarrera] = useState("");

  const [copiaA, setCopiaA] = useState("");

  const [asunto, setAsunto] = useState("");
  const [cuerpo, setCuerpo] = useState("");
  const [iaStatus, setIaStatus] = useState<{ texto: string; color: string } | null>(null);

  const [firmanteId, setFirmanteId] = useState("");
  const [firmanteTitulo, setFirmanteTitulo] = useState("");
  const [firmanteNombre, setFirmanteNombre] = useState("");
  const [firmanteCargo, setFirmanteCargo] = useState("");
  const [iniciales, setIniciales] = useState("");

  const [generando, setGenerando] = useState(false);

  useEffect(() => {
    fetch("/herramientas/oficios/api/carreras")
      .then((r) => r.json())
      .then(setCarreras);
  }, []);

  useEffect(() => {
    const url = carreraFiltro
      ? `/herramientas/oficios/api/destinatarios?carrera=${encodeURIComponent(carreraFiltro)}`
      : "/herramientas/oficios/api/destinatarios";
    fetch(url)
      .then((r) => r.json())
      .then(setDocentes);
  }, [carreraFiltro]);

  function agregarDestinatario(id: string) {
    const d = docentes.find((x) => String(x.id) === id);
    if (!d) return;
    setDestinatarioNombre((prev) => (prev ? `${prev}\n${d.nombre}` : d.nombre));
    setDestinatarioCargo((prev) => (prev ? `${prev}\n${d.cargo}` : d.cargo));
    setDestinatarioCarrera((prev) => (prev ? `${prev}\n${d.carrera}` : d.carrera));
  }

  function agregarCopia(id: string) {
    const d = docentes.find((x) => String(x.id) === id);
    if (!d) return;
    const nombreCompleto = `${d.titulo_grado} ${d.nombre}, ${d.post_grado}`;
    const linea = `${nombreCompleto} - ${d.cargo}`;
    setCopiaA((prev) => (prev ? `${prev}\n${linea}` : linea));
  }

  function seleccionarFirmante(id: string) {
    setFirmanteId(id);
    const d = docentes.find((x) => String(x.id) === id);
    if (!d) return;
    setFirmanteTitulo(d.titulo_grado);
    setFirmanteNombre(d.nombre);
    setFirmanteCargo(d.cargo);
  }

  async function mejorarConIA() {
    if (!asunto && !cuerpo) {
      setIaStatus({ texto: "⚠️ Escribe algo primero.", color: "text-red-600" });
      return;
    }
    setIaStatus({ texto: "⏳ Procesando...", color: "text-slate-500" });
    try {
      if (asunto.trim().length >= 3) {
        setAsunto(await enriquecer("oficio_asunto", asunto));
      }
      if (cuerpo.trim().length >= 3) {
        setCuerpo(await enriquecer("oficio_cuerpo", cuerpo, tono));
      } else if (asunto.trim().length >= 3) {
        setCuerpo(await enriquecer("oficio_cuerpo_generar", asunto, tono));
      }
      setIaStatus({ texto: "✅ Enriquecido. Puedes editar.", color: "text-green-600" });
    } catch (e) {
      setIaStatus({ texto: `❌ ${(e as Error).message}`, color: "text-red-600" });
    }
  }

  async function generar(e: React.FormEvent) {
    e.preventDefault();
    setGenerando(true);
    try {
      const fd = new FormData();
      fd.set("num_oficio", numOficio);
      fd.set("ciudad", ciudad);
      fd.set("fecha_emision", fecha);
      fd.set("destinatario_nombre", destinatarioNombre);
      fd.set("destinatario_cargo", destinatarioCargo);
      fd.set("destinatario_carrera", destinatarioCarrera);
      fd.set("copia_a", copiaA);
      fd.set("asunto", asunto);
      fd.set("cuerpo", cuerpo);
      fd.set("firmante_titulo", firmanteTitulo);
      fd.set("firmante_nombre", firmanteNombre);
      fd.set("firmante_cargo", firmanteCargo);
      fd.set("iniciales", iniciales);

      const r = await fetch("/herramientas/oficios/api", { method: "POST", body: fd });
      if (!r.ok) {
        const d = await r.json().catch(() => ({ error: "Error desconocido" }));
        throw new Error(d.error);
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Oficio_${numOficio || "borrador"}.docx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Error al generar el oficio: ${(e as Error).message}`);
    } finally {
      setGenerando(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-[#003366]">📄 Generador de Oficios</h1>

      <form onSubmit={generar} className="space-y-6">
        <fieldset className="rounded-lg border border-slate-300 p-4">
          <legend className="px-2 font-semibold text-[#003366]">Identificación del Oficio</legend>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-sm">
              N.º Oficio
              <input required value={numOficio} onChange={(e) => setNumOficio(e.target.value)}
                placeholder="Ej: OFICIO-001-2026" className="ht-input" />
            </label>
            <label className="block text-sm">
              Ciudad
              <input required value={ciudad} onChange={(e) => setCiudad(e.target.value)} className="ht-input" />
            </label>
            <label className="block text-sm">
              Fecha de emisión
              <input required type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} className="ht-input" />
            </label>
            <label className="block text-sm">
              Tono del oficio
              <select value={tono} onChange={(e) => setTono(e.target.value)} className="ht-input">
                {TONOS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </label>
          </div>
        </fieldset>

        <fieldset className="rounded-lg border border-slate-300 p-4">
          <legend className="px-2 font-semibold text-[#003366]">Destinatario</legend>
          <label className="mb-3 block text-sm">
            Filtrar por carrera/dependencia
            <select value={carreraFiltro} onChange={(e) => setCarreraFiltro(e.target.value)} className="ht-input">
              <option value="">-- Todas las carreras/dependencias --</option>
              {carreras.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
          <label className="mb-3 block text-sm">
            Seleccione el destinatario
            <select defaultValue="" onChange={(e) => { agregarDestinatario(e.target.value); e.target.value = ""; }} className="ht-input">
              <option value="" disabled>-- Seleccione un destinatario --</option>
              {docentes.map((d) => (
                <option key={d.id} value={d.id}>{d.titulo_grado} {d.nombre}, {d.post_grado} — {d.cargo}</option>
              ))}
            </select>
          </label>
          <label className="mb-3 block text-sm">
            Nombre completo
            <textarea required rows={2} value={destinatarioNombre} onChange={(e) => setDestinatarioNombre(e.target.value)} className="ht-input" />
          </label>
          <label className="mb-3 block text-sm">
            Cargo
            <textarea required rows={2} value={destinatarioCargo} onChange={(e) => setDestinatarioCargo(e.target.value)} className="ht-input" />
          </label>
          <label className="block text-sm">
            Carrera/Dependencia
            <textarea required rows={2} value={destinatarioCarrera} onChange={(e) => setDestinatarioCarrera(e.target.value)} className="ht-input" />
          </label>
          <p className="mt-2 text-xs text-slate-500">* Seleccione un destinatario de la lista para agregarlo. Puede seleccionar varios o editar el texto libremente.</p>
        </fieldset>

        <fieldset className="rounded-lg border border-slate-300 p-4">
          <legend className="px-2 font-semibold text-[#003366]">Con copia a (CC)</legend>
          <label className="mb-3 block text-sm">
            Seleccione personas para agregar a CC
            <select defaultValue="" onChange={(e) => { agregarCopia(e.target.value); e.target.value = ""; }} className="ht-input">
              <option value="" disabled>-- Seleccione alguien para añadir a CC --</option>
              {docentes.map((d) => (
                <option key={d.id} value={d.id}>{d.titulo_grado} {d.nombre}, {d.post_grado} — {d.cargo}</option>
              ))}
            </select>
          </label>
          <button type="button" onClick={() => setCopiaA("")} className="mb-3 rounded bg-slate-200 px-3 py-1 text-sm">Limpiar CC</button>
          <label className="block text-sm">
            Personas en CC
            <textarea rows={3} value={copiaA} onChange={(e) => setCopiaA(e.target.value)} className="ht-input" />
          </label>
        </fieldset>

        <fieldset className="rounded-lg border border-slate-300 p-4">
          <legend className="px-2 font-semibold text-[#003366]">Contenido del Oficio</legend>
          <label className="mb-3 block text-sm">
            Asunto
            <input required value={asunto} onChange={(e) => setAsunto(e.target.value)}
              placeholder="Resumen breve del oficio" className="ht-input" />
          </label>
          <label className="block text-sm">
            Cuerpo del oficio
            <textarea required rows={8} value={cuerpo} onChange={(e) => setCuerpo(e.target.value)}
              placeholder="Detalle del contenido del oficio..." className="ht-input" />
          </label>
          <div className="mt-3 flex items-center gap-3 rounded-lg border border-green-300 bg-green-50 p-3">
            <button type="button" onClick={mejorarConIA} className="rounded bg-green-600 px-4 py-1.5 text-sm font-semibold text-white">
              ✨ Mejorar con IA
            </button>
            {iaStatus && <span className={`text-sm ${iaStatus.color}`}>{iaStatus.texto}</span>}
          </div>
        </fieldset>

        <fieldset className="rounded-lg border border-slate-300 p-4">
          <legend className="px-2 font-semibold text-[#003366]">Firmante</legend>
          <label className="mb-3 block text-sm">
            Seleccione el firmante
            <select required value={firmanteId} onChange={(e) => seleccionarFirmante(e.target.value)} className="ht-input">
              <option value="" disabled>-- Seleccione un firmante --</option>
              {docentes.map((d) => (
                <option key={d.id} value={d.id}>{d.titulo_grado} {d.nombre}, {d.post_grado} — {d.cargo}</option>
              ))}
            </select>
          </label>
          <div className="grid grid-cols-3 gap-3">
            <label className="block text-sm">Título<input required readOnly value={firmanteTitulo} className="ht-input" /></label>
            <label className="block text-sm">Nombre completo<input required readOnly value={firmanteNombre} className="ht-input" /></label>
            <label className="block text-sm">Cargo<input required readOnly value={firmanteCargo} className="ht-input" /></label>
          </div>
          <label className="mt-3 block text-sm">
            Iniciales elaborador
            <input required value={iniciales} onChange={(e) => setIniciales(e.target.value)} placeholder="Ej: ARZ/ddm" className="ht-input" />
          </label>
        </fieldset>

        <button type="submit" disabled={generando}
          className="w-full rounded-lg bg-[#003366] py-3 font-semibold text-white disabled:opacity-50">
          {generando ? "Generando..." : "📄 Generar Oficio"}
        </button>
      </form>
    </main>
  );
}
