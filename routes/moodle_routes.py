import io
from flask import Blueprint, request, send_file, jsonify, render_template
from logic.moodle_logic import gift_to_moodle_xml, gift_to_preview

moodle_bp = Blueprint("moodle", __name__)


@moodle_bp.route("/util/moodle-xml")
def moodle_page():
    return render_template("moodle_xml.html")


@moodle_bp.route("/util/moodle-xml/generar", methods=["POST"])
def moodle_generar_xml():
    data = request.get_json(force=True)
    gift_text = data.get("gift_text", "")
    category = data.get("category", "").strip()

    if not gift_text.strip():
        return jsonify({"error": "El texto GIFT está vacío."}), 400

    try:
        xml_content = gift_to_moodle_xml(gift_text, category)
        filename = f"{category or 'preguntas'}.xml"
        return send_file(
            io.BytesIO(xml_content.encode("utf-8")),
            as_attachment=True,
            download_name=filename,
            mimetype="application/xml"
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {e}"}), 500


@moodle_bp.route("/util/moodle-xml/preview", methods=["POST"])
def moodle_preview():
    data = request.get_json(force=True)
    gift_text = data.get("gift_text", "")

    try:
        questions = gift_to_preview(gift_text)
        return jsonify({"questions": questions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
