# BANK OF NIAGARA — Flask demo

Quickstart — BANK OF NIAGARA (Flask)

1. Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the app (development):

```bash
# Windows PowerShell
$env:FLASK_APP = 'app.py'; $env:FLASK_ENV = 'development'; flask run --host=0.0.0.0 --port=5000
```

Alternatively, run directly:

```bash
python app.py
```

3. Data: CSV files are created under `data/` automatically. Use `/admin/migrate-ids` POST endpoint to remap user IDs (one-time helper).

4. Notes:
- This is a simple demo banking app using CSVs and no production-grade security.
- Do not use in production without adding proper authentication, password hashing, and DB.
