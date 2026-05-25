import sys
import subprocess
import time
import pandas as pd
from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

PERUSALL_SCRIPTS = Path(__file__).resolve().parent.parent / 'Perusall' / 'scripts'
UPLOADS_BASE = Path(__file__).resolve().parent.parent / 'data' / 'perusall_uploads'


def procesar_archivos_perusall(archivos: list[FileStorage], max_score: float = None) -> dict:
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    input_dir = UPLOADS_BASE / timestamp / 'input'
    out_dir = UPLOADS_BASE / timestamp / 'out'
    input_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in archivos:
        filename = secure_filename(f.filename)
        if filename:
            f.save(str(input_dir / filename))

    cmd = [sys.executable, str(PERUSALL_SCRIPTS / 'generate_report.py'),
           '--input-dir', str(input_dir),
           '--out-dir', str(out_dir)]
    if max_score is not None:
        cmd += ['--max-score', str(max_score)]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    archivos_out = []
    if out_dir.exists():
        archivos_out = [p.name for p in sorted(out_dir.iterdir()) if p.is_file()]

    preview_html = ''
    report_csv = out_dir / 'report.csv'
    if report_csv.exists():
        try:
            df = pd.read_csv(report_csv)
            cols_mostrar = ['email', 'first_name', 'last_name', 'matched', 'total_score',
                            'score_10', 'comment_count', 'avg_comment_len', 'upvotes', 'status']
            cols_presentes = [c for c in cols_mostrar if c in df.columns]
            preview_html = df[cols_presentes].head(50).to_html(
                classes='preview-table', index=False, border=0, na_rep='—'
            )
        except Exception:
            preview_html = ''

    summary_text = ''
    summary_md = out_dir / 'summary.md'
    if summary_md.exists():
        summary_text = summary_md.read_text(encoding='utf-8')

    return {
        'timestamp': timestamp,
        'archivos': archivos_out,
        'preview_html': preview_html,
        'summary': summary_text,
        'stdout': result.stdout,
        'stderr': result.stderr,
    }


def obtener_archivo_resultado(timestamp: str, filename: str) -> Path:
    safe_ts = secure_filename(timestamp)
    safe_fn = secure_filename(filename)
    path = UPLOADS_BASE / safe_ts / 'out' / safe_fn
    if not path.exists():
        raise FileNotFoundError(f'{path} no existe')
    return path
