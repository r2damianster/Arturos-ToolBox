from flask import Flask, request, render_template, send_file, redirect, url_for
import os
import sys
import subprocess
import zipfile
from pathlib import Path
from werkzeug.utils import secure_filename
import time
import pandas as pd

APP_ROOT = Path(__file__).resolve().parents[1]

app = Flask(__name__)


def make_dirs(p: Path):
    p.mkdir(parents=True, exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files:
            return render_template('index.html', error='No files uploaded')

        timestamp = time.strftime('%Y%m%d-%H%M%S')
        work_dir = APP_ROOT / 'uploads' / timestamp
        input_dir = work_dir / 'input'
        out_dir = work_dir / 'out'
        make_dirs(input_dir)
        make_dirs(out_dir)

        for f in files:
            filename = secure_filename(f.filename)
            if not filename:
                continue
            f.save(str(input_dir / filename))

        # run the existing report generator using the current python
        py = sys.executable
        gen_script = APP_ROOT / 'scripts' / 'generate_report.py'

        cmd = [py, str(gen_script), '--input-dir', str(input_dir), '--out-dir', str(out_dir)]
        subprocess.run(cmd, check=False)

        # prepare a list of output files and a small preview (report.csv)
        files_out = []
        if out_dir.exists():
            for p in sorted(out_dir.iterdir()):
                files_out.append(p.name)

        preview_html = ''
        report_csv = out_dir / 'report.csv'
        if report_csv.exists():
            try:
                df = pd.read_csv(report_csv)
                preview_html = df.head(100).to_html(classes='table', index=False, border=0)
            except Exception:
                preview_html = '<p>No se pudo generar vista previa del CSV.</p>'

        return render_template('index.html', files=files_out, timestamp=timestamp, preview_html=preview_html)

    return render_template('index.html')


@app.route('/download/<timestamp>/<filename>')
def download_file(timestamp, filename):
    work_dir = APP_ROOT / 'uploads' / timestamp
    file_path = work_dir / 'out' / filename
    if not file_path.exists():
        return 'File not found', 404
    return send_file(str(file_path), as_attachment=True)


@app.route('/generate_pdf/<timestamp>')
def generate_pdf(timestamp):
    work_dir = APP_ROOT / 'uploads' / timestamp
    out_dir = work_dir / 'out'
    pdf_script = APP_ROOT / 'scripts' / 'generate_report_pdf.py'
    py = sys.executable
    cmd = [py, str(pdf_script), '--out-dir', str(out_dir)]
    subprocess.run(cmd, check=False)
    pdf_path = out_dir / 'report.pdf'
    if not pdf_path.exists():
        return 'PDF not generated', 500
    return send_file(str(pdf_path), as_attachment=True)


@app.route('/generate_zip/<timestamp>')
def generate_zip(timestamp):
    work_dir = APP_ROOT / 'uploads' / timestamp
    input_dir = work_dir / 'input'
    out_dir = work_dir / 'out'
    zip_path = work_dir / 'bundle.zip'
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if input_dir.exists():
                for p in input_dir.rglob('*'):
                    if p.is_file():
                        zf.write(p, arcname=Path('input') / p.name)
            if out_dir.exists():
                for p in out_dir.rglob('*'):
                    if p.is_file():
                        zf.write(p, arcname=Path('out') / p.relative_to(out_dir))
    except Exception:
        return 'Error creating zip', 500
    if not zip_path.exists():
        return 'ZIP not generated', 500
    return send_file(str(zip_path), as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
