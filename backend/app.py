from pathlib import Path  # Import Path for cross-platform file paths
from flask import Flask, send_from_directory, render_template_string  # Flask web framework and utilities
import os  # Operating system utilities
# Configuration: set base and frontend directories
BASE_DIR = Path(__file__).resolve().parent.parent  # Project root directory
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')  # Frontend folder path
# Create Flask app with static file configuration
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')  # Initialize Flask app
# Route: serve main page at root URL
@app.route('/')  # Register route for '/'
def index():  # Handler function
    # Build path to HTML file
    index_path = os.path.join(FRONTEND_DIR, 'logistics-company.html')  # Full path
    # Check if file exists and serve it
    if os.path.exists(index_path):  # File check
        return send_from_directory(FRONTEND_DIR, 'logistics-company.html')  # Return HTML
    # Fallback message if file missing
    return "Frontend not found. Place files in the frontend/ folder."  # Error message
# Route: serve other static files
@app.route('/<path:filename>')  # Catch-all route for other files
def static_files(filename):  # Handler function
    # Send requested file from frontend folder
    return send_from_directory(FRONTEND_DIR, filename)  # Serve file
# App entry point
if __name__ == '__main__':  # Check if run directly
    app.run(debug=True)  # Start development server
