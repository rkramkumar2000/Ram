"""Flask webhook receiver for Google Sheets edit notifications."""

from flask import Flask, request, jsonify
import os
import subprocess
from datetime import datetime

app = Flask(__name__)

# Configuration
REPO_PATH = os.getenv('REPO_PATH', '/path/to/sheettosql')
PYTHON_PATH = os.getenv('PYTHON_PATH', 'python')

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle incoming webhook from Google Sheets."""
    try:
        data = request.get_json()
        
        # Log the edit
        log_edit(data)
        
        # Trigger SQL generation
        trigger_sql_generation()
        
        return jsonify({'status': 'success'}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

def log_edit(data):
    """Log sheet edit details."""
    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
    
    log_entry = (
        f"\n=== Sheet Edit at {timestamp} ===\n"
        f"Sheet: {data['sheetName']}\n"
        f"Editor: {data['lastEditor']}\n"
        f"Range: {data['changedRange']['a1Notation']}\n"
    )
    
    with open('sheet_edits.log', 'a') as f:
        f.write(log_entry)

def trigger_sql_generation():
    """Trigger the SQL generation script."""
    script_path = os.path.join(REPO_PATH, 'scripts', 'generate_sql.py')
    
    try:
        subprocess.run(
            [PYTHON_PATH, script_path],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running SQL generation: {e.stderr}")
        raise

if __name__ == '__main__':
    # For development only - use proper WSGI server in production
    app.run(port=5000)