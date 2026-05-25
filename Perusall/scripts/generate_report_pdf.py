#!/usr/bin/env python3
"""Generador de PDF para el reporte consolidado de Persusall."""
from pathlib import Path
import argparse
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


def parse_summary(summary_path: Path):
    summary = []
    with summary_path.open('r', encoding='utf8') as f:
        for line in f:
            if line.startswith('- **'):
                summary.append(line.strip().lstrip('- ').replace('**', ''))
    return summary


def build_student_table(report: pd.DataFrame, count=None):
    df = report.copy()
    df['normalized_score_pct'] = pd.to_numeric(df['normalized_score_pct'], errors='coerce')
    df['comment_count'] = pd.to_numeric(df['comment_count'], errors='coerce').fillna(0).astype(int)
    df['upvotes'] = pd.to_numeric(df['upvotes'], errors='coerce').fillna(0).astype(int)
    df = df.sort_values(['comment_count', 'normalized_score_pct'], ascending=[False, False])
    head = df if count is None else df.head(count)
    rows = [[
        'Email', 'Matched', 'Score', '0-100%', '0-10', 'Comments', 'Avg comment len', 'Upvotes'
    ]]
    for _, r in head.iterrows():
        rows.append([
            r.get('email', ''),
            'Sí' if str(r.get('matched')).lower() == 'true' else 'No',
            r.get('total_score', ''),
            f"{r.get('normalized_score_pct', '')}",
            f"{r.get('score_10', '')}",
            f"{int(r.get('comment_count', 0))}",
            f"{r.get('avg_comment_len', 0):.1f}",
            f"{int(r.get('upvotes', 0))}",
        ])
    return rows


def build_comparison_table(report: pd.DataFrame, count=None):
    df = report.copy()
    df['matched'] = df['matched'].astype(str).str.lower() == 'true'
    df['match_score'] = pd.to_numeric(df.get('match_score', pd.Series(dtype='float')), errors='coerce').fillna(0)
    df = df.sort_values(['matched', 'match_score'], ascending=[False, False])
    head = df if count is None else df.head(count)
    rows = [[
        'Asistencia email', 'Gradebook email', 'Gradebook nombre', 'Match type', 'Match score', 'Score', 'Comentarios'
    ]]
    for _, r in head.iterrows():
        rows.append([
            r.get('email', ''),
            r.get('gradebook_email', ''),
            r.get('gradebook_name', ''),
            r.get('gradebook_match_type', ''),
            f"{r.get('gradebook_match_score', '')}",
            r.get('total_score', ''),
            f"{int(r.get('comment_count', 0))}",
        ])
    return rows


def main():
    parser = argparse.ArgumentParser(description='Genera un PDF de reporte de Persusall')
    parser.add_argument('--out-dir', default='Medicina/out')
    parser.add_argument('--report-file', default='report.csv')
    parser.add_argument('--summary-file', default='summary.md')
    parser.add_argument('--pdf-file', default='report.pdf')
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    report_path = out_dir / args.report_file
    summary_path = out_dir / args.summary_file
    pdf_path = out_dir / args.pdf_file

    report = pd.read_csv(report_path)
    summary_lines = parse_summary(summary_path)

    doc = SimpleDocTemplate(str(pdf_path), pagesize=landscape(letter),
                            rightMargin=0.5 * inch, leftMargin=0.5 * inch,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('Reporte Persusall - Medicina', styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph('Resumen general', styles['Heading2']))
    for entry in summary_lines:
        elements.append(Paragraph(entry, styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph('Lista de estudiantes con más actividad / datos', styles['Heading2']))
    table_data = build_student_table(report, count=None)
    table = Table(table_data, repeatRows=1, hAlign='LEFT', colWidths=[2.0*inch, 0.6*inch, 0.6*inch, 0.7*inch, 0.6*inch, 0.8*inch, 0.9*inch, 0.7*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4d79ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph('Tabla de comparación de emails y nombres', styles['Heading2']))
    comparison_data = build_comparison_table(report, count=None)
    comparison_table = Table(comparison_data, repeatRows=1, hAlign='LEFT', colWidths=[2.5*inch, 2.5*inch, 2.3*inch, 1.0*inch, 0.8*inch, 0.7*inch, 0.7*inch])
    comparison_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6b75')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(comparison_table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph('Notas', styles['Heading2']))
    elements.append(Paragraph('Este PDF resume el estado actual de los datos generados a partir de Persusall y la lista de asistencia. ' \
                              'La tabla de comparación muestra la correspondencia entre el email de asistencia y el email/nombre encontrado en el gradebook, junto al tipo de match y el puntaje asociado.', styles['Normal']))

    doc.build(elements)
    print('PDF generado en', pdf_path)


if __name__ == '__main__':
    main()
