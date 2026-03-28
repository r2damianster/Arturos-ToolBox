/**
 * main.js — Caja de Utilidades
 */

// Muestra/oculta secciones del SPA
function mostrarSeccion(seccionId) {
    document.querySelectorAll('.content-section').forEach(el => el.classList.add('hidden'));
    const seccion = document.getElementById(seccionId);
    if (seccion) seccion.classList.remove('hidden');
}

// Lista los archivos seleccionados en un input[type=file]
function listarArchivos(input, divId, icono) {
    const div = document.getElementById(divId);
    if (!div) return;
    if (!input.files.length) { div.innerHTML = ''; return; }
    let html = `<strong style="font-size:0.9em;">${input.files.length} archivo(s) seleccionado(s)</strong>
                <ul style="margin:8px 0 0; padding:0; list-style:none;">`;
    for (const f of input.files) {
        html += `<li style="font-size:0.85em; padding:2px 0;">${icono} ${f.name}</li>`;
    }
    html += '</ul>';
    div.innerHTML = html;
}
