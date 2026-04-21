import hashlib
import os
import uuid
from flask import session
from werkzeug.utils import secure_filename

ALLOWED_IMAGE = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_VIDEO = {'mp4', 'mov', 'avi', 'webm'}
ALLOWED_FILE  = ALLOWED_IMAGE | ALLOWED_VIDEO | {'pdf', 'doc', 'docx', 'zip'}

def allowed(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def save_upload(file, folder):
    """Сохраняет файл, возвращает имя файла или None."""
    if not file or not file.filename:
        return None
    ext = file.filename.rsplit('.', 1)[-1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', folder, name)
    file.save(path)
    return name

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def current_user():
    if 'user_id' not in session:
        return None
    from database import get_db
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    db.close()
    return user
