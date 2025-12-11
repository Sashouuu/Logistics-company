# Logistics Company — Demo Website

Local demo website for the assignment.

Quick start (Windows):

1. Create a virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the Flask server:

```powershell
python backend\app.py
```

4. Open http://127.0.0.1:5000 in your browser.

Files:
- frontend/logistics-company.html — main page
- frontend/assets/* — CSS and JS
- backend/app.py — minimal server to serve static frontend files
