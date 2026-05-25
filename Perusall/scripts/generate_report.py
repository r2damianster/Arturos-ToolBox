#!/usr/bin/env python3
"""Generador de reporte para Persusall + lista de matriculados.

Uso: python scripts/generate_report.py --input-dir "./Medicina" --out-dir ./Medicina/out

Genera:
- report.csv: resumen por estudiante
- comments_by_student.csv: comentarios agrupados
- summary.md: resumen global
"""
from pathlib import Path
import argparse
import json
import re
import sys
import pandas as pd
from rapidfuzz import fuzz
from unidecode import unidecode


def norm(s: str) -> str:
    if pd.isna(s):
        return ""
    return unidecode(str(s)).strip().lower()


def load_csv(path: Path):
    if not path.exists():
        return None
    return pd.read_csv(path)


def build_name_key(first, last):
    return norm(f"{first} {last}")


def email_local_part(email: str) -> str:
    email = norm(email)
    if '@' in email:
        local = email.split('@', 1)[0]
    else:
        local = email
    local = local.replace('.', ' ').replace('_', ' ').replace('-', ' ')
    local = re.sub(r'\d+', ' ', local)
    return re.sub(r'\s+', ' ', local).strip()


def normalized_tokens(text: str) -> str:
    txt = norm(text)
    txt = re.sub(r'[^a-z0-9 ]', ' ', txt)
    return re.sub(r'\s+', ' ', txt).strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", default="Medicina")
    p.add_argument("--out-dir", default=None)
    p.add_argument("--max-score", type=float, default=None,
                   help="si se conoce la puntuación máxima de la tarea (ej. 3), se usa para normalizar")
    p.add_argument("--prompt-unmatched", action="store_true",
                   help="preguntar si hay estudiantes en Persusall/gradebook que no están en la lista")
    args = p.parse_args()

    input_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir or input_dir / "out")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Cargar archivos esperados
    grades_fp = next(input_dir.glob("all-grades*.csv"), None)
    gradebook_fp = next(input_dir.glob("*gradebook*.csv"), None)
    comments_fp = next(input_dir.glob("comments*.csv"), None)
    attendance_fp = next(input_dir.glob("asistencia*.csv"), None)

    grades = load_csv(grades_fp) if grades_fp else None
    gradebook = load_csv(gradebook_fp) if gradebook_fp else None
    comments = load_csv(comments_fp) if comments_fp else None
    attendance = load_csv(attendance_fp) if attendance_fp else None

    if attendance is None:
        print("No se encontró archivo de asistencia en", input_dir)
        return

    # Normalize attendance emails
    attendance = attendance.rename(columns={attendance.columns[0]: 'email'})
    attendance['email'] = attendance['email'].astype(str).str.strip()
    attendance['email_norm'] = attendance['email'].str.lower()

    # Build student map from grades (email -> name)
    student_map = {}
    name_to_email = {}
    if grades is not None:
        grades = grades.rename(columns=lambda c: c.strip())
        if 'Email address' in grades.columns:
            grades['email'] = grades['Email address'].astype(str).str.strip().str.lower()
        if 'First name' in grades.columns and 'Last name' in grades.columns:
            grades['name_key'] = grades.apply(lambda r: build_name_key(r.get('First name',''), r.get('Last name','')), axis=1)
            for _, r in grades.iterrows():
                if r.get('email') and r.get('email') != 'nan':
                    student_map[r['email']] = r
                    name_to_email[r['name_key']] = r['email']

    # Build gradebook student candidate records for fuzzy matching
    gradebook_map = {}
    gradebook_students = []
    if gradebook is not None:
        gradebook = gradebook.rename(columns=lambda c: c.strip())
        if 'Email' in gradebook.columns:
            gradebook['email'] = gradebook['Email'].astype(str).str.strip().str.lower()
        if 'First name' in gradebook.columns and 'Last name' in gradebook.columns:
            gradebook['name_key'] = gradebook.apply(lambda r: build_name_key(r.get('First name',''), r.get('Last name','')), axis=1)
            gradebook['email_local'] = gradebook['email'].apply(email_local_part)
            gradebook['name_tokens'] = gradebook['name_key'].apply(normalized_tokens)
            for _, r in gradebook.iterrows():
                if r.get('email') and r.get('email') != 'nan':
                    gradebook_map[r['email']] = r
                    gradebook_students.append(r)

    # prepare comments mapping
    comments_mapped = []
    comment_author_stats = {}
    if comments is not None:
        comments = comments.rename(columns=lambda c: c.strip())
        comments['first_name'] = comments.get('First name', '').fillna('')
        comments['last_name'] = comments.get('Last name', '').fillna('')
        comments['name_key'] = comments.apply(lambda r: build_name_key(r['first_name'], r['last_name']), axis=1)

        for name_key, group in comments.groupby('name_key'):
            if not name_key:
                continue
            first_name = group['first_name'].iloc[0]
            last_name = group['last_name'].iloc[0]
            if 'Word count' in group.columns:
                avg_len = float(group['Word count'].astype(float).mean())
            else:
                avg_len = float(group['Comment text'].astype(str).str.len().mean())
            upvotes = int(group['Upvoters'].astype(float).fillna(0).sum()) if 'Upvoters' in group.columns else 0
            comment_author_stats[name_key] = {
                'first_name': first_name,
                'last_name': last_name,
                'comment_count': int(len(group)),
                'avg_comment_len': avg_len,
                'upvotes': upvotes,
            }

    # For fuzzy matching, prepare grade name list
    grade_names = list(name_to_email.keys())

    def best_gradebook_match_by_name(name_key: str):
        if not name_key:
            return None
        best = None
        for student in gradebook_students:
            student_name = student.get('name_tokens', '')
            score = fuzz.token_sort_ratio(name_key, student_name) if student_name else 0
            if student_name and all(token in name_key for token in student_name.split() if len(token) > 2):
                score += 5
            if best is None or score > best[0]:
                best = (score, student)
        if best and best[0] >= 80:
            return best
        return None

    def best_gradebook_match(email_norm: str):
        local = email_local_part(email_norm)
        best = None
        for student in gradebook_students:
            email_local = student.get('email_local', '')
            name_tokens = student.get('name_tokens', '')
            score_email = fuzz.token_sort_ratio(local, email_local) if email_local else 0
            score_name = fuzz.token_sort_ratio(local, name_tokens) if name_tokens else 0
            score = max(score_email, score_name)
            if email_local and local == email_local:
                score = max(score, 95)
            if name_tokens and all(token in local for token in name_tokens.split() if len(token) > 2):
                score += 5
            if best is None or score > best[0]:
                best = (score, student, score_email, score_name)
        if best and best[0] >= 75:
            return best
        return None

    # Aggregate per attendance student
    rows = []
    for _, a in attendance.iterrows():
        email = a['email_norm']
        row = {
            'email': a['email'],
            'matched': False,
            'matched_by': None,
            'match_score': None,
            'first_name': None,
            'last_name': None,
            'gradebook_email': None,
            'gradebook_name': None,
            'gradebook_match_type': None,
            'gradebook_match_score': None,
            'total_score': None,
            'normalized_score_pct': None,
            'score_10': None,
            'components': None,
            'instructor_score': None,
            'comment_count': 0,
            'avg_comment_len': 0,
            'upvotes': 0,
            'status': None,
        }

        matched_student = None
        if gradebook is not None:
            if email in gradebook_map:
                matched_student = gradebook_map[email]
                row['matched_by'] = 'gradebook_email'
                row['match_score'] = 100
            else:
                candidate = best_gradebook_match(email)
                if candidate is not None:
                    score, matched_student, score_email, score_name = candidate
                    row['matched_by'] = 'gradebook_fuzzy'
                    row['match_score'] = score

        if matched_student is not None:
            row['matched'] = True
            row['first_name'] = matched_student.get('First name')
            row['last_name'] = matched_student.get('Last name')
            row['gradebook_email'] = matched_student.get('email')
            row['gradebook_name'] = f"{matched_student.get('First name','').strip()} {matched_student.get('Last name','').strip()}".strip()
            row['gradebook_match_type'] = row['matched_by']
            row['gradebook_match_score'] = row['match_score']
            row['status'] = matched_student.get('Status') or matched_student.get('Completion Status')

            # Prefer score from the grade CSV if available, else use gradebook score
            grade_row = None
            if grades is not None:
                if email in student_map:
                    grade_row = student_map[email]
                elif matched_student.get('name_key') in name_to_email:
                    grade_row = student_map.get(name_to_email[matched_student['name_key']])

            if grade_row is not None:
                row['total_score'] = grade_row.get('Score')
                comps = {c: grade_row[c] for c in grades.columns if c.startswith('Grade component')}
                row['components'] = comps
                row['instructor_score'] = grade_row.get('Grade component: Instructor score') or grade_row.get('Grade component: Instructor score', None)
            else:
                row['total_score'] = matched_student.get('Mente y ciencia cognitiva') or matched_student.get('Score')

        # match comments by name -> email
        if comments is not None and row['matched']:
            matched_comments = []
            name_key = build_name_key(row['first_name'] or '', row['last_name'] or '')
            if name_key and name_key in comments['name_key'].values:
                matched_comments = comments[comments['name_key'] == name_key].to_dict('records')
            else:
                if name_key:
                    for _, c in comments.iterrows():
                        score = fuzz.token_sort_ratio(name_key, c['name_key'])
                        if score >= 85:
                            matched_comments.append(c.to_dict())

            if len(matched_comments) > 0:
                dfc = pd.DataFrame(matched_comments)
                row['comment_count'] = int(len(dfc))
                if 'Word count' in dfc.columns:
                    row['avg_comment_len'] = float(dfc['Word count'].astype(float).mean())
                else:
                    row['avg_comment_len'] = float(dfc['Comment text'].astype(str).str.len().mean())
                if 'Upvoters' in dfc.columns:
                    row['upvotes'] = int(dfc['Upvoters'].astype(float).sum())

        # normalized score pct
        if row['total_score'] is not None and pd.notna(row['total_score']):
            try:
                val = float(row['total_score'])
                maxscore = args.max_score
                if not maxscore and grades is not None:
                    maxscore = float(grades['Score'].dropna().max()) if 'Score' in grades.columns else val
                if maxscore:
                    row['normalized_score_pct'] = round((val / float(maxscore)) * 100, 2)
                    row['score_10'] = round((val / float(maxscore)) * 10, 2)
                else:
                    row['normalized_score_pct'] = None
                    row['score_10'] = None
            except Exception:
                row['normalized_score_pct'] = None
                row['score_10'] = None

        rows.append(row)

    # Add comment-only records that do not match any attendance row
    matched_name_keys = {build_name_key(r['first_name'] or '', r['last_name'] or '') for r in rows if r['first_name'] or r['last_name']}
    for name_key, stats in comment_author_stats.items():
        if name_key in matched_name_keys:
            continue
        author_first = stats['first_name']
        author_last = stats['last_name']
        comment_row = {
            'email': '',
            'matched': False,
            'matched_by': 'comments_only',
            'match_score': None,
            'first_name': author_first,
            'last_name': author_last,
            'gradebook_email': None,
            'gradebook_name': None,
            'gradebook_match_type': None,
            'gradebook_match_score': None,
            'total_score': None,
            'normalized_score_pct': None,
            'components': None,
            'instructor_score': None,
            'comment_count': stats['comment_count'],
            'avg_comment_len': stats['avg_comment_len'],
            'upvotes': stats['upvotes'],
            'status': None,
        }
        if gradebook is not None:
            candidate = best_gradebook_match_by_name(name_key)
            if candidate is not None:
                score, matched_student = candidate
                comment_row['gradebook_email'] = matched_student.get('email')
                comment_row['gradebook_name'] = f"{matched_student.get('First name','').strip()} {matched_student.get('Last name','').strip()}".strip()
                comment_row['gradebook_match_type'] = 'gradebook_name'
                comment_row['gradebook_match_score'] = score
                comment_row['status'] = matched_student.get('Status') or matched_student.get('Completion Status')
                if grades is not None and matched_student.get('name_key') in name_to_email:
                    grade_row = student_map.get(name_to_email[matched_student['name_key']])
                    if grade_row is not None:
                        comment_row['total_score'] = grade_row.get('Score')
                        comment_row['components'] = {c: grade_row[c] for c in grades.columns if c.startswith('Grade component')}
                        comment_row['instructor_score'] = grade_row.get('Grade component: Instructor score') or grade_row.get('Grade component: Instructor score', None)
        rows.append(comment_row)

    report_df = pd.DataFrame(rows)
    report_fp = out_dir / 'report.csv'
    report_df.to_csv(report_fp, index=False)

    # comments by student (best effort)
    if comments is not None:
        comments['matched_email'] = comments['name_key'].map(name_to_email)
        comments_fp_out = out_dir / 'comments_by_student.csv'
        comments.to_csv(comments_fp_out, index=False)

    # Unmatched students in Persusall / gradebook vs lista de asistencia
    unmatched_candidates = []
    if args.prompt_unmatched and grades is not None:
        attendance_emails = set(attendance['email_norm'].tolist())
        attendance_locals = {email_local_part(e) for e in attendance_emails}
        for _, g in grades.iterrows():
            grade_email = norm(g.get('Email address', g.get('email', '')))
            grade_local = email_local_part(grade_email)
            if grade_email in attendance_emails or grade_local in attendance_locals:
                continue
            name_key = build_name_key(g.get('First name', ''), g.get('Last name', ''))
            if name_key and gradebook is not None:
                if any(fuzz.token_sort_ratio(name_key, build_name_key(r.get('First name', ''), r.get('Last name', ''))) >= 90 for _, r in gradebook.iterrows()):
                    continue
            unmatched_candidates.append({
                'email': grade_email,
                'name': f"{g.get('First name','').strip()} {g.get('Last name','').strip()}".strip(),
                'score': g.get('Score'),
            })
        if unmatched_candidates:
            print(f"\nATENCIÓN: {len(unmatched_candidates)} estudiantes aparecen en Persusall pero no en la lista de asistencia.")
            if sys.stdin.isatty():
                choice = input('¿Deseas ver el detalle de los casos no coincidentes? [y/N]: ').strip().lower()
                if choice == 'y':
                    for s in unmatched_candidates:
                        print(f" - {s['name']} <{s['email']}> score={s['score']}")
            else:
                print('Ejecutando en modo no interactivo. Usa --prompt-unmatched y un terminal interactivo para revisar los casos.')

    # summary
    summary = {
        'total_enrolled': int(len(attendance)),
        'with_grades': int(report_df['matched'].sum()),
        'avg_score_pct': float(report_df['normalized_score_pct'].dropna().mean()) if report_df['normalized_score_pct'].dropna().size>0 else None,
        'median_score_pct': float(report_df['normalized_score_pct'].dropna().median()) if report_df['normalized_score_pct'].dropna().size>0 else None,
        'avg_score_10': float(report_df['score_10'].dropna().mean()) if report_df['score_10'].dropna().size>0 else None,
        'median_score_10': float(report_df['score_10'].dropna().median()) if report_df['score_10'].dropna().size>0 else None,
        'avg_comments_per_student': float(report_df['comment_count'].mean()),
    }
    summary_fp = out_dir / 'summary.md'
    with open(summary_fp, 'w', encoding='utf8') as f:
        f.write('# Resumen de reporte\n\n')
        for k,v in summary.items():
            f.write(f'- **{k}**: {v}\n')

    print('Reportes generados en', out_dir)


if __name__ == '__main__':
    main()
