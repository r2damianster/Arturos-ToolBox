# Changelog

Todos los cambios notables en este proyecto se documentan aquí.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

### Cambios pendientes de commit
- Documentación actualizada en README.md
- Contexto del proyecto en QWEN.md

---

## [2026-04-12] — IA Enrichment + DB Docentes + Admin Panel

### ✨ Nuevo
- **Enriquecimiento con IA** (Groq/Llama 3.3 70B):
  - Botón `✨ Enriquecer con IA` en Acta Técnica (aspectos, desarrollo, compromisos)
  - Botón `✨ Enriquecer con IA` en Convocatoria Docentes (asunto, descripción)
  - Botón `✨ Enriquecer con IA` en Convocatoria Estudiantes (asunto, descripción)
  - La IA mejora el texto **in-place** en los campos del formulario (no genera el .docx directamente)
- **Rate Limiting para IA**:
  - Default: 10 minutos entre usos
  - Configurable desde Panel Admin (1–120 min)
  - Límite por IP
- **Base de Datos SQLite** (`data/docentes.db`):
  - Tabla `docentes` con campos: titulo_grado, nombre, post_grado, cargo, carrera, es_director
  - 10 docentes precargados de Pedagogía de Idiomas Nacionales y Extranjeros
  - Filas dinámicas en documentos: se adaptan al número de docentes (sin límite fijo)
- **Panel de Administración** (`/docentes/admin`):
  - Auth simple (email + contraseña)
  - CRUD completo de docentes (agregar, editar, eliminar)
  - Configuración de cooldown IA
  - Botón cerrar sesión
- **Convocatoria Docentes — Dos modos**:
  - 📋 **Carrera**: Selecciona carrera, carga docentes automáticamente
  - ✏️ **Manual**: Agrega docentes uno a uno
- **README.md** completo con documentación del proyecto
- **QWEN.md** con contexto del proyecto para sesiones futuras

### 🔧 Modificado
- `Convocatoria_Docentes.docx`: Nombres hardcodeados reemplazados por filas plantilla dinámicas
- `_form_convocatoria_docentes.html`: Dropdown desde BD + modo manual/carrera
- `convocatorias.py`: Método `_expandir_tabla_lista()` y `_expandir_tabla_firmas()` para filas dinámicas
- `app.py`: `init_db()` al inicio + nuevos blueprints
- `.gitignore`: Excluye `data/*.db`

### 📁 Archivos nuevos
- `logic/db.py` — CRUD SQLite docentes
- `logic/ia_enriquecer.py` — Servicio IA con rate limiting
- `routes/docentes_routes.py` — Auth + admin + API docentes
- `routes/ia_routes.py` — Endpoints IA (`/util/ia_enriquecer`, `/util/ia_status`, `/util/ia_config`)
- `templates/admin_docentes.html` — Panel de administración
- `templates/docentes_login.html` — Login admin
- `QWEN.md` — Contexto del proyecto
- `CHANGELOG.md` — Este archivo

---

## [2026-04-12] — Fix: Migrar transcripción a Groq Whisper

- Migración de transcripción de AssemblyAI a Groq Whisper (gratis)
- Fix: prompt de resumen evita inventar nombres de hablantes

## [2026-04-12] — Update Acta_Tecnica.docx

- Actualización del template de Acta Técnica

---

## Histórico anterior
- Ver commits en GitHub: https://github.com/r2damianster/Arturos-ToolBox/commits/master
