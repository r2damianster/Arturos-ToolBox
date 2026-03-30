from flask import Flask, render_template
from dotenv import load_dotenv
load_dotenv()
from routes.utilidades_routes import utilidades_bp
from routes.actas_routes import actas_bp
from routes.convocatorias_routes import convocatorias_bp
from routes.reportes_routes import reportes_bp
from routes.maestrias_routes import maestrias_bp
from routes.transcripcion_routes import transcripcion_bp

app = Flask(__name__)
app.register_blueprint(utilidades_bp)
app.register_blueprint(actas_bp)
app.register_blueprint(convocatorias_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(maestrias_bp)
app.register_blueprint(transcripcion_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
