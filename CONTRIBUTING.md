# 📄 Guía de Arquitectura y Desarrollo - ARTeacher

Esta guía detalla la estructura unificada del proyecto para asegurar la escalabilidad y facilitar la integración de nuevos módulos como el **Acta Técnica**.

---

## 📁 Estructura del Proyecto

El sistema sigue un patrón de diseño modular para separar la interfaz de la lógica de negocio:

* **`/routes`**: Blueprints de Flask organizados por dominio (Actas, Convocatorias, Maestrías). Mantiene el `flask_app.py` limpio.
* **`/logic`**: Inteligencia del programa. Scripts en Python para procesamiento de datos (Pandas) y manejo de documentos (`docxtpl`).
* **`/resources`**: Carpeta independiente en la raíz que almacena las plantillas maestras `.docx`.
* **`/templates/components`**: Fragmentos HTML reutilizables (formularios con prefijo `_form_` y el sidebar).
* **`/static`**: Recursos estáticos (CSS para estilos y JS para interactividad global).

---

## 🎨 Frontend: Estándares de Interfaz

### 1. Sistema de Componentes
No escribir formularios directamente en `index.html`. Crear archivos en `templates/components/` e incluirlos mediante Jinja2:
`{% include 'components/_form_nombre.html' %}`.

### 2. Navegación SPA-ish (Single Page Application)
Se utiliza `static/js/main.js` para gestionar la visibilidad de las secciones:
* Cada contenedor principal debe tener las clases `content-section hidden`.
* El sidebar invoca la función `mostrarSeccion('id_del_div')`.

### 3. Reglas de Formularios
* **Nomenclatura:** Los nombres de los inputs (`name`) deben coincidir con las variables esperadas en el Backend y los tags del Word.
* **Manejo de Fechas:** Usar `onchange="convertirFechaLarga(this, 'ID_DESTINO')"` para procesar fechas legibles automáticamente.

---

## ⚙️ Backend: Lógica y Rutas

### 1. Definición de Rutas (`/routes`)
Para cada módulo nuevo:
1.  Definir el Blueprint en su archivo correspondiente (ej: `actas_routes.py`).
2.  Registrar el Blueprint en el archivo principal `flask_app.py`.
3.  Apuntar el `action` del formulario HTML a la ruta creada.

### 2. Procesamiento (`/logic`)
* **Separación de responsabilidades:** Las rutas solo reciben datos; la generación del documento y el cálculo de datos deben vivir en clases dentro de `/logic`.
* **Carga de Plantillas:** Los métodos deben buscar los archivos base directamente en la carpeta `/resources`.

---

## 🚀 Checklist para Nuevos Módulos (Ej: Acta Técnica)

1.  **Plantilla:** Subir el archivo `.docx` a `/resources/` con los tags `{{ TAG }}` correspondientes.
2.  **Lógica:** Crear/actualizar el script en `/logic/` para procesar el nuevo tipo de documento.
3.  **Interfaz:** Crear `_form_acta_tecnica.html` usando etiquetas `<fieldset>` y `<legend>`.
4.  **Ruta:** Implementar el endpoint en `routes/actas_routes.py` para manejar el `POST`.
5.  **Sidebar:** Vincular el acceso en `_sidebar.html` con el ID de la sección.
**Regla de Oro:** Todo nuevo formulario debe estar contenido en un `<div>` que incluya estrictamente la clase `content-section`. Esto permite que `main.js` limpie la pantalla automáticamente sin necesidad de actualizar el array de secciones en el código JavaScript.
---

## 📋 Diccionario de Campos (Mapeo Word vs HTML)

### 1. Convocatorias (Docentes/Estudiantes)
| Etiqueta Word | Variable HTML / Logic | Descripción |
| :--- | :--- | :--- |
| `{{num_convocatoria}}` | `num_convocatoria` | Número secuencial (ej. 001) |
| `{{periodo}}` | `periodo` | Periodo académico actual |
| `{{ciudad}}` | `ciudad` | Sede de emisión (Default: Manta) |
| `{{fecha_larga}}` | `fecha_larga` | Fecha formateada por JS |
| `{{asunto}}` | `asunto` | Título del documento |
| `{{fecha_reunion}}` | `fecha_reunion` | Fecha del evento |
| `{{nombre}}` | `lista_estudiantes` | **Marcador de Tabla**: Llenado vía Excel |

### 2. Informe de Notas
| Etiqueta Word | Variable HTML / Logic | Descripción |
| :--- | :--- | :--- |
| `{{fecha}}` | `fecha` | Fecha de generación del informe |
| `{{titulo_destinatario}}` | `titulo_academico_destinatario` | Título del Subdecano/a |
| `{{nombres_destinatario}}` | `nombres_apellidos_destinatario`| Nombre de autoridad |
| `{{asignatura}}` | `asignatura` | Nombre de la materia (desde Excel) |
| `{{parcial_texto}}` | `info_parcial['TEXTO']` | "PRIMER" o "SEGUNDO" |

### 3. Paquete PAT (Maestrías)
| Etiqueta Word | Variable Logic | Descripción |
| :--- | :--- | :--- |
| `{{MAESTRIA}}` | `maestria` | Nombre del programa |
| `{{Responsable}}` | `responsable` | Coordinador a cargo |
| `{{NOMBRE}}` | `nombre` | Nombre del Maestrante |
| `{{Oficio}}` | `oficio` | N° de designación |
| `{{t1}}` a `{{t9}}` | `temas` | Temas de las 9 sesiones |

---

## 🛠️ Notas de Estandarización
* **CSS:** Utilizar clases globales como `.submit-btn`, `.container`, y `.textarea-flexible`.
* **Git:** El archivo `.gitignore` está configurado para omitir carpetas `__pycache__` y archivos temporales.

### ⚓ Dinamismo en Navegación
Para garantizar que los formularios no se solapen, se utiliza el selector de clase `.content-section`. 

