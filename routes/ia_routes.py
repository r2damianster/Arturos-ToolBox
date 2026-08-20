from flask import Blueprint, request, jsonify
from logic.ia_enriquecer import enriquecer_texto

ia_bp = Blueprint('ia', __name__)


@ia_bp.route('/util/ia_enriquecer', methods=['POST'])
def ia_enriquecer():
    """
    Endpoint único para enriquecer texto con IA.
    Recibe: { contexto: str, texto: str, tono: str (optional) }
    Retorna: { texto_enriquecido: str } o { error: str }
    """
    data = request.get_json(silent=True) or {}
    contexto = data.get('contexto', '').strip()
    texto = data.get('texto', '').strip()
    tono = data.get('tono', '').strip()

    if not contexto or not texto:
        return jsonify({"error": "Se requiere 'contexto' y 'texto'"}), 400

    resultado, error = enriquecer_texto(contexto, texto, tono=tono or None)
    if error:
        return jsonify({"error": error}), 500

    return jsonify({"texto_enriquecido": resultado})
