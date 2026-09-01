# Herramientas de Carrera (PINE) — carpeta portable

Esta carpeta es autocontenida: todo lo que usa son imports relativos internos
(`_lib/`, `_templates/`). Se corta completa y se pega dentro de `app/` del
proyecto `carrerapineuleam` (queda como `app/herramientas/`).

## Al pegarla en el destino

1. **Dependencias npm** — agregar a su `package.json` (o `npm install`):
   `docxtemplater pizzip docx jszip xlsx pdf-parse mammoth @neondatabase/serverless`
   (`jszip`, `xlsx` y `@neondatabase/serverless` seguramente ya están instalados ahí).

2. **Variables de entorno** (Vercel → Project Settings → Environment Variables):
   - `GROQ_API_KEY` — la misma que usa Utilidades (Flask). Modelo usado: `openai/gpt-oss-120b`.
   - `DATABASE_URL` — su Neon existente. Solo hace falta correr la migración de abajo
     una vez (agrega tablas nuevas, no toca las existentes).

3. **Migración de Neon** (una sola vez, contra el `DATABASE_URL` real del proyecto):
   correr el DDL + seed de `modalidades_titulacion`, `rubricas`, `evaluaciones`,
   `evaluacion_observaciones`, `evaluacion_indicadores` y `docentes` — ver
   `carrera-herramientas/scripts/migrate-neon.ts` en el repo de origen (Utilidades)
   para el SQL exacto y los datos de seed (rúbricas TEFL/Artículo, 13 docentes iniciales).

4. **next.config**: agregar a `experimental.serverComponentsExternalPackages` las
   entradas `"pdf-parse"` y `"pdfjs-dist"` (si no existe esa clave, crearla) —
   sin esto, `pdf-parse` rompe el build porque `pdfjs-dist` no es compatible con
   el bundling por defecto de Next para Server Components.

5. Ningún archivo subido (memo, trabajo del estudiante, fotos de evidencia) se
   guarda en disco ni en la nube — se procesa en memoria y se descarta. Esto ya
   funciona igual en Vercel (serverless) sin cambios.

## Las 5 herramientas

| Ruta | Qué genera |
|---|---|
| `/herramientas/acta-tecnica` | Acta técnica (.docx) con redacción asistida por IA + fotos de evidencia |
| `/herramientas/oficios` | Oficio formal (.docx) a partir de una plantilla |
| `/herramientas/convocatorias` | Convocatoria a docentes o estudiantes (.docx), con hoja de asistencia |
| `/herramientas/pat-maestria` | Paquete PAT-003 a PAT-006 de acompañamiento de tesis de maestría (.zip) |
| `/herramientas/pares-lectores` | Wizard de evaluación de trabajos de titulación (TEFL / Artículo científico) → Informe + Rúbrica (.zip) |

## Notas técnicas

- Los documentos con plantilla fija (Oficios, Convocatorias, PATs, Rúbricas de
  Pares Lectores) usan **docxtemplater** sobre los `.docx` en `_templates/`.
- Acta Técnica y el Informe de Pares Lectores se arman **desde cero** con la
  librería `docx` (sin plantilla) — el primero porque necesita insertar fotos
  (el módulo de imágenes de docxtemplater es de pago), el segundo porque su
  contenido ya era 100% generado por código en la versión Flask original.
- `_lib/docxtemplater.ts` limpia automáticamente marcas de Word (`w:proofErr`,
  `w:bookmarkStart/End`) que a veces parten un `{{tag}}` en dos, y usa un parser
  con `.trim()` porque docxtemplater no recorta espacios internos del tag por
  defecto (algunas plantillas traen `{{ Tag }}` con espacios).
