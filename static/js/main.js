/**
 * main.js — Arturo's ToolBox
 */

// ── Navegación SPA ──────────────────────────────────────────────────────────
function mostrarSeccion(seccionId) {
    document.querySelectorAll('.content-section').forEach(el => el.classList.add('hidden'));
    const seccion = document.getElementById(seccionId);
    if (seccion) {
        seccion.classList.remove('hidden');
    } else {
        console.warn(`Sección "${seccionId}" no existe en el DOM.`);
    }
    // Marcar botón activo en sidebar
    document.querySelectorAll('.sb-group-items button').forEach(b => b.classList.remove('sb-active'));
    const btnActivo = document.querySelector(`.sb-group-items button[onclick*="${seccionId}"]`);
    if (btnActivo) btnActivo.classList.add('sb-active');
    // Cerrar en mobile
    _cerrarSidebarMobile();
}

// ── Sidebar: colapsar/expandir (desktop + mobile overlay) ───────────────────
function toggleSidebar() {
    const sidebar  = document.getElementById('sidebar');
    const main     = document.querySelector('.main-content');
    const openBtn  = document.getElementById('sb-open');
    const overlay  = document.getElementById('sb-overlay');
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        const isOpen = sidebar.classList.contains('sb-mobile-open');
        sidebar.classList.toggle('sb-mobile-open', !isOpen);
        overlay.classList.toggle('sb-visible', !isOpen);
    } else {
        const isCollapsed = sidebar.classList.contains('sb-collapsed');
        sidebar.classList.toggle('sb-collapsed', !isCollapsed);
        main.classList.toggle('sb-collapsed', !isCollapsed);
        openBtn.classList.toggle('sb-visible', !isCollapsed);
    }
}

// Cerrar sidebar mobile al navegar
function _cerrarSidebarMobile() {
    if (window.innerWidth <= 768) {
        document.getElementById('sidebar')?.classList.remove('sb-mobile-open');
        document.getElementById('sb-overlay')?.classList.remove('sb-visible');
    }
}

// ── Sidebar: acordeón — solo un grupo abierto a la vez ──────────────────────
function toggleGrupo(grupoId) {
    const grupo   = document.getElementById(grupoId);
    const btn     = grupo ? grupo.previousElementSibling : null;
    if (!grupo) return;

    const estaAbierto = grupo.classList.contains('sb-group-open');

    // Cerrar todos los grupos primero
    document.querySelectorAll('.sb-group-items').forEach(g => g.classList.remove('sb-group-open'));
    document.querySelectorAll('.sb-group-header').forEach(b => b.classList.remove('sb-group-active'));

    // Si estaba cerrado, abrirlo
    if (!estaAbierto) {
        grupo.classList.add('sb-group-open');
        if (btn) btn.classList.add('sb-group-active');
    }
}

// ── Lista archivos en input[type=file] ──────────────────────────────────────
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

// ── Lista archivos Excel (Convocatoria Estudiantes) ─────────────────────────
function actualizarListaArchivos() {
    const input      = document.getElementById('excel_files');
    const display    = document.getElementById('lista-archivos-seleccionados');
    const selCursos  = document.getElementById('cursos-multiple');
    const numCursos  = selCursos ? Array.from(selCursos.selectedOptions).length : 0;

    if (input && input.files.length > 0) {
        let html = `<strong>Archivos a procesar: ${input.files.length}</strong>`;
        if (numCursos > 0 && input.files.length < numCursos) {
            html += ` <br><span style="color:#f0ad4e;font-size:0.85em;">⚠️ Has elegido ${numCursos} cursos pero solo subiste ${input.files.length} archivo(s).</span>`;
        }
        html += "<ul style='margin-top:10px;list-style:none;padding-left:0;'>";
        for (let i = 0; i < input.files.length; i++) {
            html += `<li>✅ ${input.files[i].name}</li>`;
        }
        html += "</ul>";
        if (display) display.innerHTML = html;
    } else if (display) {
        display.innerHTML = "<em>Ningún archivo seleccionado.</em>";
    }
}

// ── Convierte fecha YYYY-MM-DD a texto largo en español ─────────────────────
function convertirFechaLarga(input, hiddenId) {
    if (!input.value) return;
    const partes = input.value.split('-');
    const fecha  = new Date(partes[0], partes[1] - 1, partes[2]);
    const texto  = fecha.toLocaleDateString('es-ES', { day:'numeric', month:'long', year:'numeric' });
    const target = document.getElementById(hiddenId);
    if (target) target.value = texto;
}

// ── Acta Técnica: agregar fila de participante ──────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    const btnAdd = document.getElementById('add-participante');
    if (btnAdd) {
        btnAdd.addEventListener('click', function () {
            const lista = document.getElementById('lista-participantes');
            const fila  = document.createElement('div');
            fila.className = 'participante-row';
            fila.style.cssText = 'display:flex;gap:10px;margin-bottom:10px;';
            fila.innerHTML = `
                <input type="text"  name="p_titulo[]"   placeholder="Título">
                <input type="text"  name="p_nombre[]"   placeholder="Nombre"   required>
                <input type="text"  name="p_apellido[]" placeholder="Apellido" required>
                <button type="button" onclick="this.parentElement.remove()"
                    style="background:#fee2e2;color:#991b1b;border:none;border-radius:4px;padding:0 10px;cursor:pointer;">✕</button>`;
            lista.appendChild(fila);
        });
    }

    const selCursos = document.getElementById('cursos-multiple');
    if (selCursos) {
        selCursos.addEventListener('change', function () {
            const aviso = document.getElementById('aviso-cursos');
            if (aviso) aviso.style.display = (Array.from(this.selectedOptions).length > 1) ? 'block' : 'none';
            actualizarListaArchivos();
        });
    }
});
