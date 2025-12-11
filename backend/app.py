from pathlib import Path
from flask import Flask, send_from_directory, render_template_string
import os

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

@app.route('/')
def index():
    # serve the main page (choose corrected filename)
    index_path = os.path.join(FRONTEND_DIR, 'logistics-company.html')
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIR, 'logistics-company.html')
    return "Frontend not found. Place files in the frontend/ folder."

@app.route('/<path:filename>')
def static_files(filename):
    # serve any other static file from frontend
    return send_from_directory(FRONTEND_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)
