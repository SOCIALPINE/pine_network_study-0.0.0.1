import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from flask_cors import CORS
import threading
from korcen import korcen
import re

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable SocketIO

TEMPLATES_DIR = 'templates'
notices = []  # List to hold announcements

def sanitize_filename(filename):
    # Define the set of invalid characters for Windows, Unix, and macOS
    invalid_chars = r'[<>:"/\\|?*]'
    # Replace invalid characters with an underscore
    sanitized_filename = re.sub(invalid_chars, '_', filename)
    return sanitized_filename

@app.route('/')
def index():
    html_files = [f.replace('.html', '') for f in os.listdir(TEMPLATES_DIR) if f.endswith('.html') and f != 'index.html']
    return render_template('index.html', html_files=html_files)

@app.route('/submit', methods=['POST'])
def submit():
    title = request.form['user_input']
    subject = request.form['user_input1']
    if not title.startswith('/'):
        title = sanitize_filename(title)
    # Check for inappropriate content
    if not title.startswith('/') and (korcen.check(title) or korcen.check(subject)):
        title = "This post has been censored."
        subject = "This post has been censored."
    else:
        if title.startswith('/'):  # If the title starts with '/', treat it as a notice
            notices.append(subject)
            socketio.emit('shoot', subject)  # Send announcement to all clients
        else:
            # Generate HTML file for the new post
            file_path = os.path.join(TEMPLATES_DIR, f"{title}.html")
            with open(file_path, "w", encoding='utf-8') as f:
                code = f"""
<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>{title}</title></head>
<body><h1>{title}</h1><h2>{subject}</h2><form action="/back" method="POST">
        <button type="돌아가기">돌아가기</button>
</form></body>
</html>
"""
                f.write(code)

            # Notify all clients about the new post
            socketio.emit('new_post', {'title': title, 'subject': subject})
            
    return index()

@app.route('/back', methods=['POST'])
def back():
    return index()

@app.route('/view/<filename>')
def view(filename):
    file_path = os.path.join(TEMPLATES_DIR, f'{filename}.html')
    if os.path.exists(file_path):
        return render_template(f'{filename}.html')
    else:
        return f"File {filename}.html not found.", 404

if __name__ == '__main__':
    print("Starting Flask application...")
    socketio.run(app, host='0.0.0.0', port=5000)
