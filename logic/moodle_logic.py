import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


def _cdata(text):
    return f"<![CDATA[{text}]]>"


def _add_text_elem(parent, tag, text, fmt=None, use_cdata=False):
    elem = ET.SubElement(parent, tag)
    if fmt:
        elem.set("format", fmt)
    txt = ET.SubElement(elem, "text")
    txt.text = _cdata(text) if use_cdata else (text or "")
    return elem


def _parse_gift(source: str) -> list:
    """Parse GIFT format into list of question dicts."""
    questions = []

    # Strip comment lines
    lines = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        lines.append(line)

    text = "\n".join(lines)

    # Split on question blocks: ::name:: ... { ... }
    # Also support questions without ::name::
    pattern = re.compile(
        r"(?:::([^:]+)::)?\s*(.*?)\s*\{(.*?)\}",
        re.DOTALL
    )

    for m in pattern.finditer(text):
        name = (m.group(1) or "").strip()
        question_text = m.group(2).strip()
        body = m.group(3).strip()

        if not question_text and not name:
            continue

        q = _classify_question(name, question_text, body)
        if q:
            questions.append(q)

    return questions


def _classify_question(name, question_text, body):
    body_stripped = body.strip()

    # True/False: {TRUE} or {FALSE}
    if re.match(r"^(TRUE|FALSE|true|false|VERDADERO|FALSO|verdadero|falso)$", body_stripped):
        correct = body_stripped.upper() in ("TRUE", "VERDADERO")
        return {
            "type": "truefalse",
            "name": name or question_text[:50],
            "text": question_text,
            "correct": correct,
        }

    # Numerical: {#answer} or {#answer:tolerance}
    if body_stripped.startswith("#"):
        num_match = re.match(r"#\s*([\d.\-]+)(?::(\d+(?:\.\d+)?))?", body_stripped)
        if num_match:
            return {
                "type": "numerical",
                "name": name or question_text[:50],
                "text": question_text,
                "answer": num_match.group(1),
                "tolerance": num_match.group(2) or "0",
            }

    # Essay: empty body
    if not body_stripped:
        return {
            "type": "essay",
            "name": name or question_text[:50],
            "text": question_text,
        }

    # Short answer: body has no ~ or = lines starting with those chars
    lines = [l.strip() for l in body_stripped.splitlines() if l.strip()]
    has_choices = any(l.startswith("~") or l.startswith("=") for l in lines)

    if not has_choices and lines:
        # Short answer — each line is an accepted answer
        return {
            "type": "shortanswer",
            "name": name or question_text[:50],
            "text": question_text,
            "answers": lines,
        }

    # Multiple choice
    choices = []
    for line in lines:
        if line.startswith("="):
            choices.append({"text": line[1:].strip(), "correct": True})
        elif line.startswith("~"):
            choices.append({"text": line[1:].strip(), "correct": False})

    if choices:
        return {
            "type": "multichoice",
            "name": name or question_text[:50],
            "text": question_text,
            "choices": choices,
        }

    return None


def _build_xml(questions: list, category: str = "") -> str:
    quiz = ET.Element("quiz")

    if category:
        cat_q = ET.SubElement(quiz, "question")
        cat_q.set("type", "category")
        cat_elem = ET.SubElement(cat_q, "category")
        _add_text_elem(cat_elem, "text", f"$course$/{category}")

    for q in questions:
        qtype = q["type"]
        question = ET.SubElement(quiz, "question")
        question.set("type", qtype)

        _add_text_elem(question, "name", q["name"])
        _add_text_elem(question, "questiontext", q["text"], fmt="html", use_cdata=True)
        _add_text_elem(question, "generalfeedback", "", fmt="html")

        dg = ET.SubElement(question, "defaultgrade")
        dg.text = "1.0000000"
        pen = ET.SubElement(question, "penalty")
        pen.text = "0.3333333"
        hid = ET.SubElement(question, "hidden")
        hid.text = "0"

        if qtype == "multichoice":
            single = ET.SubElement(question, "single")
            single.text = "true"
            shuffle = ET.SubElement(question, "shuffleanswers")
            shuffle.text = "true"
            numbering = ET.SubElement(question, "answernumbering")
            numbering.text = "abc"
            _add_text_elem(question, "correctfeedback", "Respuesta correcta.", fmt="html")
            _add_text_elem(question, "partiallycorrectfeedback", "Respuesta parcialmente correcta.", fmt="html")
            _add_text_elem(question, "incorrectfeedback", "Respuesta incorrecta.", fmt="html")

            for choice in q["choices"]:
                ans = ET.SubElement(question, "answer")
                ans.set("fraction", "100" if choice["correct"] else "0")
                ans.set("format", "html")
                txt = ET.SubElement(ans, "text")
                txt.text = _cdata(choice["text"])
                _add_text_elem(ans, "feedback", "", fmt="html")

        elif qtype == "truefalse":
            correct_text = "verdadero" if q["correct"] else "falso"
            wrong_text = "falso" if q["correct"] else "verdadero"
            for frac, txt_val in [("100", correct_text), ("0", wrong_text)]:
                ans = ET.SubElement(question, "answer")
                ans.set("fraction", frac)
                ans.set("format", "moodle_auto_format")
                txt = ET.SubElement(ans, "text")
                txt.text = txt_val

        elif qtype == "shortanswer":
            usecase = ET.SubElement(question, "usecase")
            usecase.text = "0"
            for a in q.get("answers", []):
                ans = ET.SubElement(question, "answer")
                ans.set("fraction", "100")
                ans.set("format", "moodle_auto_format")
                txt = ET.SubElement(ans, "text")
                txt.text = a

        elif qtype == "numerical":
            ans = ET.SubElement(question, "answer")
            ans.set("fraction", "100")
            ans.set("format", "moodle_auto_format")
            txt = ET.SubElement(ans, "text")
            txt.text = q["answer"]
            tol = ET.SubElement(ans, "tolerance")
            tol.text = q.get("tolerance", "0")

        elif qtype == "essay":
            ans = ET.SubElement(question, "answer")
            ans.set("fraction", "0")
            ans.set("format", "html")
            ET.SubElement(ans, "text")

    raw = ET.tostring(quiz, encoding="unicode")

    # Pretty print via minidom
    dom = minidom.parseString(f'<?xml version="1.0" encoding="UTF-8"?>{raw}')
    pretty = dom.toprettyxml(indent="  ", encoding=None)
    # Remove the extra declaration minidom adds (we already have one)
    lines = pretty.splitlines()
    if lines[0].startswith("<?xml"):
        lines = lines[1:]
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(lines)


def gift_to_moodle_xml(gift_text: str, category: str = "") -> str:
    questions = _parse_gift(gift_text)
    if not questions:
        raise ValueError("No se encontraron preguntas en el texto GIFT.")
    return _build_xml(questions, category)


def gift_to_preview(gift_text: str) -> list:
    """Return parsed questions as list of dicts for frontend preview."""
    return _parse_gift(gift_text)
