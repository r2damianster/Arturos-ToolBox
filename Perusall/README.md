# Report generator for Persusall data

Scripts to generate a consolidated report from Persusall exports and an attendance list.

Quick start

1. Create a virtualenv and install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the generator (assumes `Medicina` folder inside repository):

```powershell
python scripts\generate_report.py --input-dir "Medicina" --out-dir "Medicina\out"
```

Outputs placed in `Medicina/out`:
- `report.csv` — resumen por estudiante
- `comments_by_student.csv` — comentarios con posible email mapeado
- `summary.md` — estadísticas básicas

Notes
- The script usa emparejamiento por email y heurísticas de nombre (fuzzy). Ajusta `--max-score` si conoces la puntuación máxima.
- Podemos mejorar la asignación con embeddings / Groq según quieras.
