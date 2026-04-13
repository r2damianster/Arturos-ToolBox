# 🧰 Arturo's ToolBox

Aplicación web Flask para la gestión de documentos académicos de la **Universidad Estatal Amazónica (ULEAM)**. Genera actas técnicas, convocatorias, transcripciones, informes de notas y documentos de maestría en formato Word (.docx), con soporte de IA para enriquecimiento de texto.

---

## 📋 Tabla de Contenidos

- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Funcionalidades](#-funcionalidades)
  - [📝 Acta Técnica con IA](#-acta-técnica-con-ia)
  - [👨‍🏫 Convocatoria a Docentes](#-convocatoria-a-docentes)
  - [🎓 Convocatoria a Estudiantes](#-convocatoria-a-estudiantes)
  - [📦 Documentos PAT Maestría](#-documentos-pat-maestría)
  - [🎙️ Transcripción de Audio](#-transcripción-de-audio)
  - [📉 Informe de Notas](#-informe-de-notas)
  - [🛠️ Utilidades](#-utilidades)
- [🤖 Enriquecimiento con IA](#-enriquecimiento-con-ia)
- [🗄️ Base de Datos de Docentes](#-base-de-datos-de-docentes)
- [🔐 Panel de Administración](#-panel-de-administración)
- [Despliegue](#-despliegue)
- [Estructura del Proyecto](#-estructura-del-proyecto)

---

## 🔧 Requisitos

- Python 3.10+
- API Keys (opcionales pero recomendadas):
  - **GROQ_API_KEY** — Para enriquecimiento con IA (Llama 3.3 70B) y transcripción de audio (Whisper)

## 🚀 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/r2damianster/Arturos-ToolBox.git
cd Arturos-ToolBox

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno (opcional)
# Crear archivo .env con:
GROQ_API_KEY=tu_api_key_aqui
SECRET_KEY=una-clave-secreta-aleatoria
# ASSEMBLYAI_API_KEY ya no se requiere (transcripción migrada a Groq Whisper)

# 5. Ejecutar
python app.py
# Acceder a http://localhost:10000
```

## 📖 Uso

La aplicación se organiza en secciones accesibles desde el menú lateral (sidebar):

### 📝 Acta Técnica con IA
Genera actas técnicas universitarias con:
- Información general de la reunión (número, fecha, lugar, horario)
- Lista de participantes/firmantes
- **✨ Enriquecer con IA**: Mejora automáticamente los campos de puntos del orden del día, desarrollo de la reunión y compromisos.
- 🎙️ Extracción de notas desde audio (AssemblyAI)
- Evidencias fotográficas opcionales

### 👨‍🏫 Convocatoria a Docentes
Genera convocatorias dirigidas a docentes con:
- Dos modos de operación:
  - **📋 Docentes de la carrera**: Selecciona una carrera y carga automáticamente todos los docentes registrados en la BD.
  - **✏️ Ingresar manualmente**: Agrega docentes uno a uno (título, nombre, post-grado, cargo).
- **✨ Enriquecer con IA**: Mejora el asunto y la descripción del motivo.
- Lista de asistencia y firmas generadas dinámicamente.

### 🎓 Convocatoria a Estudiantes
Genera convocatorias para estudiantes con:
- Selección múltiple de cursos/niveles
- Carga de archivos Excel con listas de estudiantes
- **✨ Enriquecer con IA**: Mejora el asunto y descripción.

### 📦 Documentos PAT Maestría
Genera documentos del proceso de Patrón para la Maestría:
- PAT-03, PAT-04, PAT-05, PAT-06
- Soporte para diferentes líneas de investigación

### 🎙️ Transcripción de Audio
Transcribe archivos de audio a texto usando **Groq Whisper** (`whisper-large-v3`, gratuito).
Genera automáticamente un resumen estructurado en 3 secciones (Puntos Tratados, Desarrollo, Acuerdos) usando Groq LLM.
Descarga el resultado como archivo `.txt` con timestamps por segmento.

### 📉 Informe de Notas
Genera informes de notas para estudiantes.

### 🛠️ Utilidades
- 🔲 Generador de códigos QR
- 🖼️ Generador de presentaciones PPTX
- 📎 Unir imágenes a PDF
- 📂 Crear estructura de carpetas
- 📄 Convertir archivos a PDF
- 🗜️ Reducir imágenes
- 📚 CSV → BibTeX
- 📊 Generar estadísticas
- 📈 Pre-test / Post-test

---

## 🤖 Enriquecimiento con IA

La aplicación usa **Groq (Llama 3.3 70B)** para mejorar el texto que el usuario escribe en los formularios. **No genera documentos directamente** — solo enriquece los campos del formulario para que el usuario los revise y edite antes de generar el .docx.

### Contextos disponibles
| Contexto | Campos que enriquece |
|---|---|
| `acta_aspectos` | Puntos del orden del día |
| `acta_desarrollo` | Desarrollo de la reunión |
| `acta_compromisos` | Acuerdos y compromisos |
| `convocatoria_asunto` | Asunto de convocatoria |
| `convocatoria_descripcion` | Descripción/motivo |

### Rate Limiting
- Por defecto: **10 minutos** entre cada uso de IA.
- Configurable desde el **Panel de Administración** → **Configuración IA**.
- El contador es por IP (todos los usuarios comparten el límite).

### Variables de entorno
```env
GROQ_API_KEY=gsk_...         # Requerida para IA (enrichment + transcripción)
IA_COOLDOWN_SECONDS=600      # Opcional: cooldown inicial en segundos (default: 600)
```

---

## 🗄️ Base de Datos de Docentes

Se usa **SQLite** (`data/docentes.db`) para gestionar los docentes de forma dinámica:

- **Campos por docente**: `titulo_grado`, `nombre`, `post_grado`, `cargo`, `carrera`, `es_director`
- La BD se crea automáticamente al iniciar la app.
- Los docentes se usan en convocatorias y actas.
- Las filas en los documentos .docx se generan **dinámicamente**: si hay 5, 10 o 50 docentes, el documento se adapta.

---

## 🔐 Panel de Administración

Acceso: **Sidebar → ⚙️ Gestión Docentes** → Login

**Credenciales por defecto:**
- Email: `arturo.rodriguez@uleam.edu.ec`
- Contraseña: `Uleam2026`

**Funcionalidades del panel:**
1. **🤖 Configuración IA**: Intervalo entre usos de IA (1–120 minutos).
2. **👨‍🏫 Gestión de Docentes**: Agregar, editar y eliminar docentes con título, nombre, post-grado, cargo y carrera.
3. **🚪 Cerrar sesión**.

> ⚠️ Las credenciales están hardcodeadas en `routes/docentes_routes.py`. Para producción, cambiar `ADMIN_EMAIL` y `ADMIN_PASS`.

---

## 🌐 Despliegue

### Render.com
```bash
# El proyecto usa gunicorn para producción
# Configurar en Render:
# - Build Command: pip install -r requirements.txt
# - Start Command: gunicorn app:app
# - Variables de entorno: GROQ_API_KEY, ASSEMBLYAI_API_KEY, SECRET_KEY
```

### Vercel
Configuración en `vercel.json` incluida.

### Netlify
Configuración en `netlify.toml` incluida.

---

## 📁 Estructura del Proyecto

```
Utilidades/
├── app.py                      # Entry point Flask
├── gunicorn.conf.py            # Config para producción
├── requirements.txt            # Dependencias
├── .env                        # Variables de entorno (no git)
│
├── logic/
│   ├── actas_logic.py          # Lógica de Acta Técnica (usa Groq IA)
│   ├── convocatorias.py        # Generación de convocatorias (.docx)
│   ├── ia_enriquecer.py        # Servicio de enriquecimiento con IA
│   ├── db.py                   # CRUD SQLite para docentes
│   ├── PatsMaestria.py         # Documentos de maestría
│   ├── transcripcion_logic.py  # Transcripción AssemblyAI
│   ├── utilidades.py           # Funciones auxiliares
│   └── PATS/                   # Templates PAT específicos
│
├── routes/
│   ├── actas_routes.py         # Endpoints actas
│   ├── convocatorias_routes.py # Endpoints convocatorias
│   ├── docentes_routes.py      # API + admin docentes
│   ├── ia_routes.py            # Endpoint enriquecimiento IA
│   ├── maestrias_routes.py     # Endpoints maestría
│   ├── reportes_routes.py      # Endpoints reportes
│   ├── transcripcion_routes.py # Endpoints transcripción
│   └── utilidades_routes.py    # Endpoints utilidades
│
├── templates/
│   ├── base.html               # Layout base
│   ├── index.html              # Página principal
│   ├── admin_docentes.html     # Panel de administración
│   ├── docentes_login.html     # Login admin
│   └── components/
│       ├── _form_acta_tecnica.html
│       ├── _form_convocatoria_docentes.html
│       ├── _form_convocatoria_estudiantes.html
│       ├── _form_informe_notas.html
│       ├── _form_transcripcion.html
│       └── _sidebar.html
│
├── resources/                  # Templates .docx base
│   ├── Acta_Tecnica.docx
│   ├── Convocatoria_Docentes.docx
│   ├── Convocatoria_Estudiantes.docx
│   ├── NotasMenores.docx
│   └── PAT-*.docx
│
├── data/                       # BD SQLite (no git)
│   └── docentes.db
│
└── scripts/                    # Scripts auxiliares
```
