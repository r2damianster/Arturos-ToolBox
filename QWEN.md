# 🧰 Arturo's ToolBox — Contexto del Proyecto

> **Última actualización**: 2026-04-12

## Stack
- **Backend**: Flask (Python 3.12)
- **BD**: SQLite (`data/docentes.db`) — auto-generada al iniciar
- **IA**: Groq (Llama 3.3 70B) — enriquecimiento de texto
- **Audio**: AssemblyAI — transcripción
- **Docs**: python-docx + docxtpl — generación .docx
- **Server prod**: Gunicorn (Render.com)

## Arquitectura
```
app.py → configura rutas → registra blueprints desde routes/
routes/ → recibe HTTP → llama a logic/
logic/ → genera .docx desde templates en resources/
templates/ → HTML forms (sidebar navega a secciones)
```

## Blueprints registrados
| Blueprint | Ruta base | Función |
|---|---|---|
| utilidades_bp | `/util/...` | QR, PPTX, PDF, carpetas, imágenes, estadísticas |
| actas_bp | `/util/acta_tecnica` | Generar actas técnicas con IA |
| convocatorias_bp | `/util/convocatoria_*` | Convocatorias docentes/estudiantes |
| docentes_bp | `/docentes/...` | CRUD docentes + admin panel |
| ia_bp | `/util/ia_enriquecer` | Enriquecimiento de texto con Groq |
| maestrias_bp | `/util/maestria` | Documentos PAT Maestría |
| transcripcion_bp | `/util/transcripcion` | Transcripción audio |
| reportes_bp | `/util/...` | Informes de notas |

## Base de Datos de Docentes
- **Tabla**: `docentes(id, titulo_grado, nombre, post_grado, cargo, carrera, es_director)`
- **Seed**: 10 docentes de Pedagogía de Idiomas Nacionales y Extranjeros
- **Uso**: Convocatorias generan filas dinámicamente (sin límite fijo)

## IA Enriquecimiento
- **Endpoint**: `POST /util/ia_enriquecer`
- **Contextos**: `acta_aspectos`, `acta_desarrollo`, `acta_compromisos`, `convocatoria_asunto`, `convocatoria_descripcion`
- **Rate limit**: Default 10 min, configurable desde admin panel
- **Flujo**: Usuario escribe → click "✨ Enriquecer con IA" → IA mejora texto in-place → usuario edita → genera .docx

## Panel de Administración
- **URL**: `/docentes/login` → `/docentes/admin`
- **Credenciales**: `arturo.rodriguez@uleam.edu.ec` / `Uleam2026`
- **Funciones**: Configurar cooldown IA, CRUD docentes, cerrar sesión

## Convocatoria Docentes — Dos modos
1. **Carrera**: Selecciona carrera → carga todos los docentes de esa carrera desde BD
2. **Manual**: Agrega docentes uno a uno con título, nombre, post-grado, cargo

## Variables de Entorno
```env
GROQ_API_KEY=gsk_...           # IA enrichment
ASSEMBLYAI_API_KEY=...         # Transcripción audio
SECRET_KEY=...                 # Sessions Flask
IA_COOLDOWN_SECONDS=600        # Opcional: cooldown inicial
PORT=10000                     # Puerto del servidor
```

## Convenciones
- Español en UI, código en inglés (nombres de funciones/variables)
- Los `.docx` templates usan `{{PLACEHOLDER}}` que se reemplazan con `reemplazar_en_documento()`
- Las filas de tablas en convocatorias se generan dinámicamente (`add_row()`)
- Rate limiting de IA es en memoria (no persistente entre reinicios)

## Archivos clave a revisar antes de trabajar
- `logic/convocatorias.py` — Generación de convocatorias con filas dinámicas
- `logic/ia_enriquecer.py` — Servicio IA con rate limiting
- `logic/db.py` — CRUD SQLite docentes
- `routes/ia_routes.py` — Endpoints IA
- `routes/docentes_routes.py` — Auth + admin + API docentes
