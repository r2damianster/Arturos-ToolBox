from flask import Flask, render_template
from dotenv import load_dotenv
import os
import logging
from logic.db import init_db

# Inicializar base de datos de docentes
init_db()

# Configurar logs para ver qué pasa en Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

def configurar_rutas(app):
    # Lista de blueprints a registrar
    blueprints = [
        ('routes.utilidades_routes', 'utilidades_bp'),
        ('routes.actas_routes', 'actas_bp'),
        ('routes.convocatorias_routes', 'convocatorias_bp'),
        ('routes.reportes_routes', 'reportes_bp'),
        ('routes.maestrias_routes', 'maestrias_bp'),
        ('routes.transcripcion_routes', 'transcripcion_bp'),
        ('routes.docentes_routes', 'docentes_bp'),
        ('routes.ia_routes', 'ia_bp')
    ]

    for module_path, bp_name in blueprints:
        try:
            # Importación dinámica: solo falla este módulo si hay error
            import importlib
            module = importlib.import_module(module_path)
            blueprint = getattr(module, bp_name)
            app.register_blueprint(blueprint)
            logger.info(f"✔ Cargado exitosamente: {bp_name}")
        except Exception as e:
            logger.error(f"❌ Error cargando {bp_name}: {str(e)}")

configurar_rutas(app)

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except:
        return {"status": "Servidor activo", "note": "index.html no encontrado"}, 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    # debug=True es genial para local, pero Render usa Gunicorn (que ignora esto)
    app.run(host='0.0.0.0', port=port, debug=True)