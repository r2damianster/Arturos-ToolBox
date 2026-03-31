from flask import Flask, render_template
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Importación de blueprints
from routes.utilidades_routes import utilidades_bp
from routes.actas_routes import actas_bp
from routes.convocatorias_routes import convocatorias_bp
from routes.reportes_routes import reportes_bp
from routes.maestrias_routes import maestrias_bp
from routes.transcripcion_routes import transcripcion_bp

# Inicialización de la app
app = Flask(__name__)

# Registro de blueprints
app.register_blueprint(utilidades_bp)
app.register_blueprint(actas_bp)
app.register_blueprint(convocatorias_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(maestrias_bp)
app.register_blueprint(transcripcion_bp)

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Ejecución local / compatible con Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)