"""
Regenera el template Acta_Tecnica.docx con placeholders individuales para firmantes.
Usa {{firmante_1_nombre}}, {{firmante_1_cargo}}, etc. hasta 10.
"""

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def crear_template():
    doc = Document()
    
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)
    
    # TITULO
    titulo = doc.add_heading('ACTA T\xc9CNICA', level=1)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in titulo.runs:
        run.font.size = Pt(16)
        run.font.name = 'Arial'
    
    # INFO GENERAL
    t_info = doc.add_table(rows=6, cols=2)
    t_info.style = 'Table Grid'
    campos = [
        ("N\xc2\xb0 Acta:", "{{numero_acta}}"),
        ("Fecha:", "{{fecha_larga}}"),
        ("Lugar:", "{{lugar}}"),
        ("Hora de inicio:", "{{hora_inicio}}"),
        ("Hora de finalizaci\xc3\xb3n:", "{{hora_fin}}"),
        ("Convocado por:", "{{convocante_nombre}}\n{{convocante_cargo}}"),
    ]
    for i, (label, valor) in enumerate(campos):
        p_l = t_info.cell(i, 0).paragraphs[0]
        p_l.paragraph_format.space_before = Pt(2)
        p_l.paragraph_format.space_after = Pt(2)
        r = p_l.add_run(label)
        r.bold = True
        r.font.size = Pt(10)
        r.font.name = 'Arial'
        
        p_v = t_info.cell(i, 1).paragraphs[0]
        p_v.paragraph_format.space_before = Pt(2)
        p_v.paragraph_format.space_after = Pt(2)
        r = p_v.add_run(valor)
        r.font.size = Pt(10)
        r.font.name = 'Arial'
        t_info.cell(i, 0).width = Cm(4)
        t_info.cell(i, 1).width = Cm(12)
    
    doc.add_paragraph('')
    
    # PARTICIPANTES
    h_part = doc.add_heading('PARTICIPANTES', level=2)
    for run in h_part.runs:
        run.font.name = 'Arial'
    p_part = doc.add_paragraph("{{tabla_participantes}}")
    p_part.runs[0].font.size = Pt(10)
    p_part.runs[0].font.name = 'Arial'
    
    # DESARROLLO
    h_dev = doc.add_heading('DESARROLLO DE LA REUNI\xc3\x93N', level=2)
    for run in h_dev.runs:
        run.font.name = 'Arial'
    t_dev = doc.add_table(rows=3, cols=1)
    t_dev.style = 'Table Grid'
    for idx, txt in enumerate(["Puntos del orden del d\xc3\xada:", "{{aspectos_ia}}", "{{desarrollo_ia}}"]):
        p = t_dev.cell(idx, 0).paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(txt)
        r.font.size = Pt(10)
        r.font.name = 'Arial'
        if idx == 0:
            r.bold = True
    
    # COMPROMISOS
    h_comp = doc.add_heading('COMPROMISOS Y ACUERDOS', level=2)
    for run in h_comp.runs:
        run.font.name = 'Arial'
    p_comp = doc.add_paragraph("{{compromisos_ia}}")
    p_comp.runs[0].font.size = Pt(10)
    p_comp.runs[0].font.name = 'Arial'
    
    # EVIDENCIAS
    h_evid = doc.add_heading('EVIDENCIAS FOTOGR\xc3\x81FICAS', level=2)
    for run in h_evid.runs:
        run.font.name = 'Arial'
    p_evid = doc.add_paragraph("[Espacio para evidencias fotogr\xc3\xa1ficas]")
    p_evid.paragraph_format.space_before = Pt(20)
    p_evid.paragraph_format.space_after = Pt(20)
    
    # FIRMANTES - tabla con 10 filas de placeholders individuales
    h_firm = doc.add_heading('FIRMANTES', level=2)
    for run in h_firm.runs:
        run.font.name = 'Arial'
    
    # 1 header + 10 data rows = 11 filas
    t_firm = doc.add_table(rows=11, cols=2)
    t_firm.style = 'Table Grid'
    
    # Header
    for j, txt in enumerate(["NOMBRE Y CARGO", "FIRMA"]):
        p = t_firm.cell(0, j).paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(txt)
        r.bold = True
        r.font.size = Pt(10)
        r.font.name = 'Arial'
    
    # 10 filas de firmantes
    for i in range(1, 11):
        p_nombre = t_firm.cell(i, 0).paragraphs[0]
        p_nombre.paragraph_format.space_before = Pt(2)
        p_nombre.paragraph_format.space_after = Pt(2)
        r_nombre = p_nombre.add_run("{{firmante_" + str(i) + "_nombre}}")
        r_nombre.font.size = Pt(10)
        r_nombre.font.name = 'Arial'
        p_nombre.add_run("\n")
        r_cargo = p_nombre.add_run("{{firmante_" + str(i) + "_cargo}}")
        r_cargo.font.size = Pt(9)
        r_cargo.font.name = 'Arial'
        
        t_firm.cell(i, 1).paragraphs[0].add_run("")
        t_firm.cell(i, 0).width = Cm(10)
        t_firm.cell(i, 1).width = Cm(6)
    
    doc.add_paragraph('')
    
    # ELABORADO POR
    p_elab = doc.add_paragraph()
    p_elab.paragraph_format.space_before = Pt(12)
    r_elab_label = p_elab.add_run("Elaborado por: ")
    r_elab_label.bold = True
    r_elab_label.font.size = Pt(10)
    r_elab_label.font.name = 'Arial'
    r_elab_val = p_elab.add_run("{{elaborado_titulo}} {{elaborado_nombre}}")
    r_elab_val.font.size = Pt(10)
    r_elab_val.font.name = 'Arial'
    
    # Guardar
    out_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'Acta_Tecnica.docx')
    doc.save(out_path)
    print(f"✅ Template generado en: {out_path}")
    print(f"   10 slots de firmantes configurados")

if __name__ == '__main__':
    crear_template()
