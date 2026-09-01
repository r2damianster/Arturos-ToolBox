import fs from "node:fs";
import path from "node:path";
import PizZip from "pizzip";
import Docxtemplater from "docxtemplater";

const TEMPLATES_DIR = path.join(process.cwd(), "app", "herramientas", "_templates");

export type PlantillaDatos = Record<string, unknown>;

/**
 * Renderiza una plantilla .docx de `_templates/` reemplazando sus tags {{ }}.
 * Soporta loops ({#tag}...{/tag}) si la plantilla los trae.
 */
/**
 * Word inserta elementos vacíos (marcas de revisión ortográfica/gramatical, saltos de
 * página renderizados, marcadores) en medio del texto de un párrafo. Cuando caen DENTRO
 * de un tag {{ }}, parten el tag en dos <w:r> y docxtemplater ya no lo reconoce (queda
 * como texto literal sin reemplazar). Se eliminan porque son elementos vacíos/autocontenidos:
 * quitarlos no cambia el contenido visible del documento.
 */
function limpiarXmlDeMarcasDeWord(xml: string): string {
  return xml
    .replace(/<w:proofErr\b[^/]*\/>/g, "")
    .replace(/<w:bookmarkStart\b[^/]*\/>/g, "")
    .replace(/<w:bookmarkEnd\b[^/]*\/>/g, "")
    .replace(/<w:lastRenderedPageBreak\s*\/>/g, "");
}

/**
 * Igual al parser por defecto de docxtemplater (ver node_modules/docxtemplater/js/doc-utils.js),
 * pero recortando espacios: algunas plantillas (PATs) traen tags como "{{ No }}" en vez de
 * "{{No}}" y docxtemplater no recorta el contenido del tag antes de buscarlo en el contexto.
 */
function parserConTrim(tag: string) {
  const limpio = tag.trim();
  return {
    get(scope: unknown) {
      if (limpio === ".") return scope;
      if (scope && typeof scope === "object" && Object.prototype.hasOwnProperty.call(scope, limpio)) {
        return (scope as Record<string, unknown>)[limpio];
      }
      return undefined;
    },
  };
}

export function renderizarPlantilla(nombreArchivo: string, datos: PlantillaDatos): Buffer {
  const rutaPlantilla = path.join(TEMPLATES_DIR, nombreArchivo);
  const contenido = fs.readFileSync(rutaPlantilla, "binary");
  const zip = new PizZip(contenido);
  const documentXmlPath = "word/document.xml";
  zip.file(documentXmlPath, limpiarXmlDeMarcasDeWord(zip.file(documentXmlPath)!.asText()));
  const doc = new Docxtemplater(zip, {
    paragraphLoop: true,
    linebreaks: true,
    delimiters: { start: "{{", end: "}}" },
    nullGetter: () => "",
    parser: parserConTrim,
  });
  doc.render(datos);
  return doc.getZip().generate({ type: "nodebuffer", compression: "DEFLATE" });
}

/**
 * Fusiona varios buffers .docx (todos generados a partir de la MISMA plantilla base,
 * documentos de una sola sección) en uno solo, insertando salto de página entre cada uno.
 * Reemplaza el uso de `docxcompose` en Python (ver logic/PATS/Pat04.py).
 */
export function fusionarDocx(buffers: Buffer[]): Buffer {
  if (buffers.length === 0) throw new Error("fusionarDocx: no hay documentos para fusionar");
  if (buffers.length === 1) return buffers[0];

  const zips = buffers.map((buf) => new PizZip(buf));
  const xmls = zips.map((zip) => zip.file("word/document.xml")!.asText());

  const SECT_PR_RE = /<w:sectPr\b[\s\S]*?<\/w:sectPr>/;
  const BODY_RE = /<w:body\b[^>]*>([\s\S]*)<\/w:body>/;

  const PAGE_BREAK = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>';

  const cuerpos: string[] = [];
  let sectPrFinal = "";

  xmls.forEach((xml, idx) => {
    const bodyMatch = BODY_RE.exec(xml);
    if (!bodyMatch) throw new Error("fusionarDocx: documento sin <w:body>");
    let cuerpo = bodyMatch[1];

    const sectPrMatch = SECT_PR_RE.exec(cuerpo);
    if (sectPrMatch) {
      if (idx === xmls.length - 1) sectPrFinal = sectPrMatch[0];
      cuerpo = cuerpo.replace(SECT_PR_RE, "");
    }

    cuerpos.push(idx === 0 ? cuerpo : PAGE_BREAK + cuerpo);
  });

  const cuerpoFinal = cuerpos.join("") + sectPrFinal;
  const xmlFinal = xmls[0].replace(BODY_RE, `<w:body>${cuerpoFinal}</w:body>`);

  const zipFinal = zips[0];
  zipFinal.file("word/document.xml", xmlFinal);
  return zipFinal.generate({ type: "nodebuffer", compression: "DEFLATE" });
}
