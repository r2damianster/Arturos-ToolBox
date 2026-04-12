from flask import Blueprint, request, jsonify
from logic.ia_enriquecer import enriquecer_texto, check_rate_limit, record_usage, get_cooldown_seconds, set_cooldown_seconds

ia_bp = Blueprint('ia', __name__)


@ia_bp.route('/util/ia_enriquecer', methods=['POST'])
def ia_enriquecer():
    """
    Endpoint único para enriquecer texto con IA.
    Recibe: { contexto: str, texto: str, user_id: str (optional) }
    Retorna: { texto_enriquecido: str } o { error: str, cooldown_remaining: int }
    """
    data = request.get_json(silent=True) or {}
    contexto = data.get('contexto', '').strip()
    texto = data.get('texto', '').strip()
    user_id = data.get('user_id', request.remote_addr or 'global')

    if not contexto or not texto:
        return jsonify({"error": "Se requiere 'contexto' y 'texto'"}), 400

    # Rate limiting
    allowed, remaining = check_rate_limit(user_id)
    if not allowed:
        cooldown_secs = get_cooldown_seconds()
        mins = remaining // 60
        secs = remaining % 60
        return jsonify({
            "error": f"Debes esperar antes de usar la IA nuevamente.",
            "cooldown_remaining": remaining,
            "cooldown_formatted": f"{mins}m {secs}s"
        }), 429

    # Enriquecer
    resultado, error = enriquecer_texto(contexto, texto)
    if error:
        return jsonify({"error": error}), 500

    # Registrar uso
    record_usage(user_id)

    return jsonify({"texto_enriquecido": resultado})


@ia_bp.route('/util/ia_status', methods=['GET'])
def ia_status():
    """Consulta el estado del rate limit para un usuario."""
    user_id = request.args.get('user_id', request.remote_addr or 'global')
    allowed, remaining = check_rate_limit(user_id)
    cooldown_secs = get_cooldown_seconds()
    return jsonify({
        "allowed": allowed,
        "cooldown_seconds": cooldown_secs,
        "remaining_seconds": remaining,
        "cooldown_formatted": f"{remaining // 60}m {remaining % 60}s" if not allowed else "Listo"
    })


@ia_bp.route('/util/ia_config', methods=['POST'])
def ia_config():
    """Configura el cooldown (solo admin debería acceder)."""
    data = request.get_json(silent=True) or {}
    minutes = data.get('cooldown_minutes')
    if minutes is None:
        return jsonify({"error": "Se requiere 'cooldown_minutes'"}), 400
    try:
        minutes = int(minutes)
        if minutes < 1 or minutes > 120:
            return jsonify({"error": "El intervalo debe ser entre 1 y 120 minutos"}), 400
        set_cooldown_seconds(minutes * 60)
        return jsonify({"message": f"Cooldown configurado a {minutes} minutos"})
    except (ValueError, TypeError):
        return jsonify({"error": "Valor inválido"}), 400
