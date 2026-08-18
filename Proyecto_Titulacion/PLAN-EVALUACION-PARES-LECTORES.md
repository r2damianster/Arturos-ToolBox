# Plan: Módulo de Evaluación de Pares Lectores (Titulación)

**Alcance de este documento:** solo la carpeta actual (`TEFL/` y `Artifuclo/`). No se revisó ni se asume nada de otros proyectos/repos. Foco: qué documentos debe llenar el evaluador (par lector) y cómo estructurar una herramienta que lo automatice.

---

## 1. Qué debe entregar el evaluador (par lector)

Por cada trabajo asignado (notificado vía memo de Comisión Académica), el evaluador entrega **2 documentos**:

1. **Informe de Criterios Observados** — memo de respuesta con observaciones de forma y fondo.
2. **Rúbrica(s) de calificación** — específica de la modalidad de titulación del trabajo.

Ambos en sobre cerrado, plazo **5 días hábiles** desde la notificación (política 6.1 literal bb) del Manual de Titulación ULEAM: si no se entrega a tiempo, el trabajo se aprueba automáticamente con nota máxima **10**). Este plazo se calcula desde la fecha del memo.

---

## 2. Documento 1 — Informe de Criterios Observados

Archivo idéntico en `TEFL/` y `Artifuclo/` → **es una plantilla única, agnóstica de modalidad**. Reutilizable sin cambios entre TEFL, Artículo, y cualquier modalidad futura.

Campos a llenar (mapeados a las tablas del `.docx`):

**Cabecera (texto libre, fuera de tabla):**
- N.º de memorando (viene del memo de Comisión Académica, ej. `Uleam-FET-CA-ATRS-2026-1-PINE-009`)
- Título y nombre del tutor/a del trabajo
- Fecha (lugar, dd/mm/aa)
- Al cierre: título académico, nombre y firma del evaluador (miembro del tribunal), correo institucional

**Tabla 1 — datos del trabajo (4 columnas):**
| Facultad y/o Extensión | Carrera | Opción de Titulación | Título |
|---|---|---|---|

**Tabla 2 — criterios observados (matriz "Componentes / Observaciones"):**

*Aspectos formales:*
- Uso de normas APA
- Carátula
- Tamaño del papel
- Marginado
- Interlineado
- Tipo de letra
- Uso de negrilla
- Uso de citas
- Bibliografía
- Certificado del tutor/a
- Otros (según guía de la modalidad) — **campo abierto**, aquí es donde entran observaciones específicas de TEFL o de Artículo si aplica

*Aspectos de fondo:*
- Definición y formulación del contexto de investigación
- Planteamiento de objetivos
- Diseño metodológico
- Otros — **campo abierto**

Cada fila tiene una celda de observación en texto libre. El evaluador marca solo lo que amerita corrección (fila vacía = sin observación en ese componente).

---

## 3. Documento 2 — Rúbrica(s) (varía por modalidad)

### Modalidad TEFL Application Process

Un solo archivo (`PAT-04-F-001-...Con Rubricas Completo.docx`) con **4 tablas**, todas se llenan siempre juntas (no hay elección de sub-tipo dentro de TEFL):

| # | Tabla | Criterios | Escala |
|---|---|---|---|
| a | Rúbrica general — Trabajo Escrito | 8: Presentación, Introducción, Módulo 1 (FMU/Journal), Módulo 2 (Speaking-ECRIF), Módulo 3 (PDP-Listening), Módulo 4 (PDP-Reading), Módulo 5 (Writing), Conclusiones y Recomendaciones | Peso (1.00–1.50) → YES/NO → Puntaje |
| b | Speaking Lesson Plan (ECRIF) | 9 criterios (EC Stage, RI Stage, Fluently Use Stage, Time control, Teacher Talking Time ×3) | Peso (1–2) → YES/NO |
| c | PDP Lesson Plan | 10 criterios (duración 45 min, action points, objetivo, pre/during/post stage, materiales...) | YES/NO simple, sin peso |
| d | Writing Lesson Plan | 9 criterios (Preparation, Drafting/revision/editing, Extension, Time control, Teacher Talking Time ×3) | Peso (1–2) → YES/NO |

Encabezado a llenar: Estudiante, Evaluador, Fecha, **Calificación Total: ___/10** (calculado).

### Modalidad Artículo Científico / Capítulo de Libro

**3 rúbricas existen como anexos separados, pero solo 2 aplican** al proceso de par lector (confirmado por el usuario: la sustentación oral no se evalúa aquí):

| Rúbrica | Aplica | Criterios | Escala |
|---|---|---|---|
| Anexo 1 — Trabajo ORAL | ❌ Excluida (fuera de alcance) | — | — |
| Anexo 2 — Escrito **NO publicado** | ✅ (si el artículo aún no está publicado) | 6: Título y resumen (1.00), Introducción (1.50), Metodología (2.50), Desarrollo/body (2.00), Discusión y conclusiones (2.00), Cohesión/coherencia/estilo (1.00) | 4 niveles: No adecuado 0% / Poco adecuado 35% / Adecuado 70% / Totalmente adecuado 100%, ponderado por peso → Calif. + Comentarios |
| Anexo 2 — Escrito **publicado** | ✅ (si ya está publicado) | 2: Artículo/capítulo publicado (peso 7, evidencia: carta de aceptación), Evidencia de revisión de pares ciegos (peso 3, evidencia: 1 lector vs 2 lectores pares ciegos) | Escala especial con celdas N/A en niveles intermedios |

El evaluador debe **elegir cuál de las dos** según el estado real de publicación del artículo del estudiante (dato que se conoce al momento de evaluar, no viene en el memo).

Encabezado a llenar en ambas: Título del artículo, Nombre del miembro del tribunal, Fecha, Total ponderado (`/10`).

---

## 4. Datos que trae el memo de Comisión Académica (fuente de precarga)

Ambos memos (`Memo-ATRS-2026-1-PINE-009` y `-013`) comparten formato:

- N.º de memorando
- Fecha de emisión (Manta, [día])
- Lista de pares lectores/tribunal (nombres, rol "Miembro del Tribunal")
- Tema del proyecto o núcleo problémico
- Modalidad (texto libre, ej. "TEFL Application Process" / "Artículo Científico")
- Carrera
- Plazo de entrega (5 días hábiles desde notificación → **fecha límite calculable**)
- Cláusula de aprobación automática si vence el plazo

Estos campos alimentan directamente la cabecera y Tabla 1 del Informe de Criterios Observados (punto 2). Con OCR/extracción de texto + un poco de IA se puede precargar el formulario desde el PDF del memo, siempre dejando los campos editables antes de confirmar.

---

## 5. Estructura de la herramienta propuesta

### 5.1 Modelo de datos (genérico, extensible a futuras modalidades)

```
modalidades_titulacion (id, slug, nombre, requiere_subtipo)
    → 'tefl'      (requiere_subtipo = false)
    → 'articulo'  (requiere_subtipo = true: publicado | no_publicado)

rubricas (id, modalidad_id, slug, subtipo, plantilla_docx, schema_json)
    → tefl_completa            (4 tablas, ver 3.a-d)
    → articulo_no_publicado    (1 tabla, 6 criterios, escala 4 niveles)
    → articulo_publicado       (1 tabla, 2 criterios, escala especial)

evaluaciones (id, numero_memo, fecha_memo, fecha_limite, facultad, carrera,
              opcion_titulacion, titulo_trabajo, estudiante, tutor,
              evaluador_nombre, modalidad_id, rubrica_id,
              archivo_memo, archivo_trabajo, estado)

evaluacion_observaciones (id, evaluacion_id, seccion['formal'|'fondo'],
                           componente, observacion)   -- tabla 2 del Informe

evaluacion_indicadores (id, evaluacion_id, tabla_idx, criterio_idx,
                         criterio_texto, peso, respuesta, calificacion,
                         comentario, sugerencia_ia)    -- filas de la rúbrica
```

`schema_json` por rúbrica describe: tipo de escala (`yes_no` o `niveles_4`), lista de tablas y sus criterios con peso — así el formulario y el cálculo de puntaje son **data-driven**, sin `if modalidad == 'tefl'` repartido por el código.

**Agregar una modalidad nueva en el futuro** = insertar fila en `modalidades_titulacion` + `rubricas`, subir la(s) plantilla(s) `.docx` y generar su `schema_json` (script utilitario que parsea las tablas con `python-docx`, una sola vez por rúbrica). No requiere tocar la lógica del wizard ni del generador de documentos.

### 5.2 Flujo de usuario (una sola pantalla, wizard corto)

1. **Datos del memo** — formulario con los campos del punto 4 (N.º memo, fecha, facultad, carrera, título, estudiante, tutor, evaluador). Opcional: subir el PDF del memo y precargar por IA/regex, siempre editable.
2. **Modalidad** — selector poblado desde `modalidades_titulacion`. Si `requiere_subtipo` (caso Artículo), segundo selector Publicado/No publicado → determina la rúbrica exacta (la oral nunca aparece como opción).
3. **Subir el trabajo del estudiante** (`.docx`/`.pdf`) — se extrae texto para mostrarlo y para dar contexto a la IA en el paso 4.
4. **Pantalla dividida:**
   - Izquierda: visor del trabajo del estudiante.
   - Derecha: rúbrica interactiva generada desde `schema_json` (radio YES/NO o selector de 4 niveles + comentario por criterio), con botón **"Sugerir con IA"** por fila (Groq, usando el criterio + fragmento relevante del texto del estudiante) — sugerencia editable, nunca autoaplicada.
   - Debajo/aparte: tabla de Observaciones (formales/fondo) del Informe, edición libre.
   - Puntaje total recalculado en vivo según la fórmula de la rúbrica activa.
5. **Autosave** continuo (documentos largos, no se puede perder trabajo).
6. **Generar y descargar** — rellena las plantillas `.docx` con los datos capturados y entrega los 2 archivos (Informe + Rúbrica), individual o en `.zip`. Marca la evaluación como finalizada.

Extra útil: contador visual de días hábiles restantes hasta la fecha límite (dado el efecto de aprobación automática si se vence).

### 5.3 Generación de los documentos de salida

- **Informe de Criterios Observados:** un único generador (python-docx), llena cabecera + Tabla 1 + Tabla 2 fila por fila desde `evaluacion_observaciones`. Mismo código para cualquier modalidad.
- **Rúbrica:** un generador que recorre `schema_json` y escribe, por cada criterio, la marca YES/NO o el nivel elegido, el comentario, y calcula/escribe el total ponderado en el encabezado. El mismo generador sirve para TEFL (4 tablas) y Artículo (1 tabla), porque la estructura viene del `schema_json`, no está hardcodeada.

---

## 6. Fases sugeridas

| Fase | Alcance |
|---|---|
| 1 | Modelar y cargar el catálogo inicial: TEFL (4 tablas) + Artículo-publicado + Artículo-no-publicado, con sus `schema_json` generados a mano/con script |
| 2 | Wizard pasos 1-3 (memo, modalidad/subtipo, subida de archivo) sin IA |
| 3 | Render de rúbrica data-driven + cálculo de puntaje en vivo |
| 4 | Generación y descarga de los 2 documentos (MVP funcional sin IA) |
| 5 | Precarga de datos del memo por IA + botón "Sugerir con IA" por criterio |
| 6 | Contador de plazo (5 días hábiles) + script para dar de alta modalidades nuevas sin tocar código |

---

## 7. Fuera de alcance / pendiente de confirmar

- Rúbrica de sustentación oral de Artículo: excluida de este módulo por decisión del usuario.
- Contenido de los trabajos del estudiante (`Informe Journal - Naylin Moreno.pdf`, `ARTICULO ANTHONY y JHONNY.docx`) no se analizó — son solo el insumo que el evaluador lee dentro de la herramienta, no información de diseño.
