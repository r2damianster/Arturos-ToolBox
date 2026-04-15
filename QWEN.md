# 🧰 Arturo's ToolBox — Contexto del Proyecto

> **Última actualización**: 2026-04-13

## Stack
- **Backend**: Flask (Python 3.12)
- **BD**: SQLite (`data/docentes.db`) — auto-generada al iniciar
- **IA**: Groq (Llama 3.3 70B) — enriquecimiento de texto + resumen de transcripciones
- **Audio**: Groq Whisper (`whisper-large-v3`) — transcripción de audio (gratuito)
- **Docs**: python-docx + docxtpl — generación .docx
- **Server prod**: Gunicorn (Render.com)
- **AssemblyAI**: ya NO se usa (migrado a Groq Whisper)

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
| oficios_bp | `/util/oficio_*` | Generador de oficios con IA |

## Base de Datos de Docentes
- **Tabla**: `docentes(id, titulo_grado, nombre, post_grado, cargo, carrera, es_director)`
- **Seed**: 13 docentes (10 PINE + Decano Facultad + Director Investigación ULEAM + Vicerrectora Académica ULEAM)
- **Uso**: Convocatorias y oficios generan filas dinámicamente (sin límite fijo)
- **Funciones extra**: `get_docentes_by_carrera(carrera)`, `get_all_carreras()`

## Módulo Oficios (NUEVO)
- **Template**: `resources/HOJA_CARRERA_PINE.docx` (hoja membretada PINE)
- **Endpoint principal**: `POST /util/oficio_generar`
- **Endpoints auxiliares**: `GET /util/oficio_carreras`, `GET /util/oficio_destinatarios`
- **IA Contextos**: `oficio_asunto`, `oficio_cuerpo`
- **Tonos disponibles**: formal, cordial, directo, urgente
- **Flujo**: Selecciona destinatario → Elige firmante → Escribe asunto/cuerpo → (Opcional: IA enriquece) → Genera .docx

## IA Enriquecimiento
- **Endpoint**: `POST /util/ia_enriquecer`
- **Contextos**: `acta_aspectos`, `acta_desarrollo`, `acta_compromisos`, `convocatoria_asunto`, `convocatoria_descripcion`, `oficio_asunto`, `oficio_cuerpo`
- **Rate limit**: Default 10 min, configurable desde admin panel
- **Flujo**: Usuario escribe → click "✨ Enriquecer con IA" → IA mejora texto in-place → usuario edita → genera .docx

## Panel de Administración
- **URL**: `/docentes/login` → `/docentes/admin`
- **Credenciales**: `arturo.rodriguez@uleam.edu.ec` / `Uleam2026`
- **Funciones**: Configurar cooldown IA, CRUD docentes, cerrar sesión

## Convocatoria Docentes — Dos modos
1. **Carrera**: Selecciona carrera → carga todos los docentes de esa carrera desde BD
2. **Manual**: Agrega docentes uno a uno con título, nombre, post-grado, cargo

## IA Transcripción
- **Motor**: Groq Whisper (`whisper-large-v3`) — sincrónico
- **Resumen**: Groq LLM (Llama 3.3 70B) en 3 secciones: Puntos Tratados, Desarrollo, Acuerdos
- **Salida**: Archivo .txt con resumen estructurado + transcript formateado con timestamps

## Variables de Entorno
```env
GROQ_API_KEY=gsk_...           # IA enrichment + transcripción audio
SECRET_KEY=...                 # Sessions Flask
IA_COOLDOWN_SECONDS=600        # Opcional: cooldown inicial
PORT=10000                     # Puerto del servidor
# ASSEMBLYAI_API_KEY ya no se requiere
```

## Convenciones
- Español en UI, código en inglés (nombres de funciones/variables)
- Los `.docx` templates usan `{{PLACEHOLDER}}` que se reemplazan con `reemplazar_en_documento()`
- Las filas de tablas en convocatorias se generan dinámicamente (`add_row()`)
- Rate limiting de IA es en memoria (no persistente entre reinicios)

## Archivos clave a revisar antes de trabajar
- `logic/convocatorias.py` — Generación de convocatorias con filas dinámicas
- `logic/oficios_logic.py` — Generación de oficios con IA y tonos personalizables
- `logic/ia_enriquecer.py` — Servicio IA (Groq/Llama) con rate limiting
- `logic/transcripcion_logic.py` — Transcripción Groq Whisper + resumen LLM
- `logic/db.py` — CRUD SQLite docentes + funciones get_docentes_by_carrera, get_all_carreras
- `routes/ia_routes.py` — Endpoints IA
- `routes/oficios_routes.py` — Endpoints oficios
- `routes/docentes_routes.py` — Auth + admin + API docentes

## Uso con múltiples asistentes IA
Este proyecto mantiene archivos de contexto para distintos asistentes:
- **CLAUDE.md** — Instrucciones para Claude Code
- **QWEN.md** — Contexto para Qwen Code / otras IAs (este archivo)
- Ambos archivos deben mantenerse sincronizados con el estado real del proyecto
