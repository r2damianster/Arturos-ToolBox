from flask import Blueprint, request, render_template, jsonify, session, redirect, url_for
from logic.db import init_db, get_all_docentes, get_docente, add_docente, update_docente, delete_docente
from functools import wraps

docentes_bp = Blueprint('docentes', __name__)

# Credenciales de administrador
ADMIN_EMAIL = "arturo.rodriguez@uleam.edu.ec"
ADMIN_PASS = "Uleam2026"

def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('docentes.login'))
        return f(*args, **kwargs)
    return decorated

# --------------- Login / Logout ---------------
@docentes_bp.route('/docentes/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if email == ADMIN_EMAIL and password == ADMIN_PASS:
            session['admin_logged_in'] = True
            session['admin_email'] = email
            return redirect(url_for('docentes.admin_docentes'))
        return render_template('docentes_login.html', error="Credenciales incorrectas")
    return render_template('docentes_login.html')

@docentes_bp.route('/docentes/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    return redirect(url_for('docentes.login'))

# --------------- Página de administración ---------------
@docentes_bp.route('/docentes/admin')
@requires_admin
def admin_docentes():
    docentes = get_all_docentes()
    return render_template('admin_docentes.html', docentes=docentes, admin_email=session.get('admin_email'))

# --------------- API REST ---------------

# GET /docentes/api — lista todos
@docentes_bp.route('/docentes/api', methods=['GET'])
def api_list():
    return jsonify(get_all_docentes())

# GET /docentes/api/<id> — detalle
@docentes_bp.route('/docentes/api/<int:docente_id>', methods=['GET'])
def api_get(docente_id):
    d = get_docente(docente_id)
    if d:
        return jsonify(d)
    return jsonify({"error": "Docente no encontrado"}), 404

# POST /docentes/api — crear
@docentes_bp.route('/docentes/api', methods=['POST'])
def api_add():
    data = request.get_json()
    nombre = data.get('nombre', '').strip()
    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400

    new_id = add_docente(
        titulo_grado=data.get('titulo_grado', 'Lic.'),
        nombre=nombre,
        post_grado=data.get('post_grado', ''),
        cargo=data.get('cargo', 'Docente'),
        carrera=data.get('carrera', 'Pedagogía de los Idiomas Nacionales y Extranjeros'),
        es_director=data.get('es_director', False)
    )
    return jsonify({"id": new_id, "message": "Docente agregado"}), 201

# PUT /docentes/api/<id> — actualizar
@docentes_bp.route('/docentes/api/<int:docente_id>', methods=['PUT'])
def api_update(docente_id):
    data = request.get_json()
    nombre = data.get('nombre', '').strip()
    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400

    update_docente(
        docente_id,
        titulo_grado=data.get('titulo_grado', 'Lic.'),
        nombre=nombre,
        post_grado=data.get('post_grado', ''),
        cargo=data.get('cargo', 'Docente'),
        carrera=data.get('carrera', 'Pedagogía de los Idiomas Nacionales y Extranjeros'),
        es_director=data.get('es_director', False)
    )
    return jsonify({"message": "Docente actualizado"})

# DELETE /docentes/api/<id> — eliminar
@docentes_bp.route('/docentes/api/<int:docente_id>', methods=['DELETE'])
def api_delete(docente_id):
    delete_docente(docente_id)
    return jsonify({"message": "Docente eliminado"})


# --------------- API para formulario de convocatoria ---------------
# GET /docentes/api/lista — retorna solo nombre+cargo para dropdowns
@docentes_bp.route('/docentes/api/lista', methods=['GET'])
def api_lista():
    docentes = get_all_docentes()
    return jsonify(docentes)
