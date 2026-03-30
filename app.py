from flask import Flask, render_template, jsonify
from routes.utilidades_routes import utilidades_bp

app = Flask(__name__)
app.register_blueprint(utilidades_bp)

import_errors = []

try:
    from routes.actas_routes import actas_bp
    app.register_blueprint(actas_bp)
except Exception as e:
    import_errors.append(f"actas_routes: {e}")

try:
    from routes.convocatorias_routes import convocatorias_bp
    app.register_blueprint(convocatorias_bp)
except Exception as e:
    import_errors.append(f"convocatorias_routes: {e}")

try:
    from routes.reportes_routes import reportes_bp
    app.register_blueprint(reportes_bp)
except Exception as e:
    import_errors.append(f"reportes_routes: {e}")

try:
    from routes.maestrias_routes import maestrias_bp
    app.register_blueprint(maestrias_bp)
except Exception as e:
    import_errors.append(f"maestrias_routes: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug')
def debug():
    return jsonify({
        "status": "ok",
        "import_errors": import_errors
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
