from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from utils import current_user, hash_password, allowed, save_upload, ALLOWED_IMAGE, ALLOWED_FILE, ALLOWED_VIDEO

bp = Blueprint('cabinet', __name__, template_folder='templates')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        city = request.form.get('city', '').strip()
        if not email or not password or not name:
            flash('Заполните все обязательные поля')
            return render_template('register.html')
        db = get_db()
        existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('Email уже зарегистрирован')
            db.close()
            return render_template('register.html')
        db.execute('INSERT INTO users (name, email, phone, city, password_hash) VALUES (?,?,?,?,?)',
                   (name, email, phone, city, hash_password(password)))
        db.commit()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()
        session['user_id'] = user['id']
        return redirect(url_for('cabinet.cabinet'))
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ? AND password_hash = ?',
                          (email, hash_password(password))).fetchone()
        db.close()
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('cabinet.cabinet'))
        flash('Неверный email или пароль')
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('showcase.index'))

@bp.route('/cabinet')
def cabinet():
    user = current_user()
    if not user:
        return redirect(url_for('cabinet.login'))
    db = get_db()
    orders = db.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (user['id'],)).fetchall()
    db.close()
    return render_template('cabinet.html', orders=orders)

@bp.route('/cabinet/profile', methods=['GET', 'POST'])
def cabinet_profile():
    user = current_user()
    if not user:
        return redirect(url_for('cabinet.login'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        city = request.form.get('city', '').strip()
        bio = request.form.get('bio', '').strip()
        db = get_db()
        avatar_file = request.files.get('avatar')
        avatar_name = None
        if avatar_file and avatar_file.filename and allowed(avatar_file.filename, ALLOWED_IMAGE):
            avatar_name = save_upload(avatar_file, 'images/avatars')
        if avatar_name:
            db.execute('UPDATE users SET name=?, phone=?, city=?, bio=?, avatar=? WHERE id=?',
                       (name, phone, city, bio, avatar_name, user['id']))
        else:
            db.execute('UPDATE users SET name=?, phone=?, city=?, bio=? WHERE id=?',
                       (name, phone, city, bio, user['id']))
        db.commit()
        db.close()
        flash('Профиль сохранён', 'success')
        return redirect(url_for('cabinet.cabinet_profile'))
    return render_template('cabinet_profile.html')

@bp.route('/cabinet/messages')
@bp.route('/cabinet/messages/<int:to_id>', methods=['GET', 'POST'])
def cabinet_messages(to_id=None):
    user = current_user()
    if not user:
        return redirect(url_for('cabinet.login'))
    db = get_db()
    dialogs = db.execute('''SELECT u.id, u.name, u.avatar, u.role,
        (SELECT content FROM messages WHERE (from_user_id=u.id AND to_user_id=?) OR (from_user_id=? AND to_user_id=u.id) ORDER BY created_at DESC LIMIT 1) as last_msg,
        (SELECT created_at FROM messages WHERE (from_user_id=u.id AND to_user_id=?) OR (from_user_id=? AND to_user_id=u.id) ORDER BY created_at DESC LIMIT 1) as last_time,
        (SELECT COUNT(*) FROM messages WHERE from_user_id=u.id AND to_user_id=? AND is_read=0) as unread
        FROM users u WHERE u.id IN (
            SELECT DISTINCT CASE WHEN from_user_id=? THEN to_user_id ELSE from_user_id END
            FROM messages WHERE from_user_id=? OR to_user_id=?
        ) ORDER BY last_time DESC''',
        (user['id'], user['id'], user['id'], user['id'], user['id'], user['id'], user['id'], user['id'])).fetchall()
    chat_msgs = []
    interlocutor = None
    if to_id:
        if request.method == 'POST':
            content = request.form.get('content', '').strip()
            attach_file = request.files.get('attachment')
            attach_name = None
            attach_type = None
            if attach_file and attach_file.filename and allowed(attach_file.filename, ALLOWED_FILE):
                attach_name = save_upload(attach_file, 'uploads/messages')
                ext = attach_file.filename.rsplit('.', 1)[-1].lower()
                if ext in ALLOWED_IMAGE:
                    attach_type = 'image'
                elif ext in ALLOWED_VIDEO:
                    attach_type = 'video'
                else:
                    attach_type = 'file'
            if content or attach_name:
                db.execute('INSERT INTO messages (from_user_id, to_user_id, content, attachment, attachment_type) VALUES (?,?,?,?,?)',
                           (user['id'], to_id, content, attach_name, attach_type))
                db.commit()
                return redirect(url_for('cabinet.cabinet_messages', to_id=to_id))
        db.execute('UPDATE messages SET is_read=1 WHERE from_user_id=? AND to_user_id=?', (to_id, user['id']))
        db.commit()
        chat_msgs = db.execute('''SELECT m.*, u.name as sender_name FROM messages m
            LEFT JOIN users u ON m.from_user_id = u.id
            WHERE (m.from_user_id=? AND m.to_user_id=?) OR (m.from_user_id=? AND m.to_user_id=?)
            ORDER BY m.created_at''', (user['id'], to_id, to_id, user['id'])).fetchall()
        interlocutor = db.execute('SELECT * FROM users WHERE id=?', (to_id,)).fetchone()
    db.close()
    return render_template('cabinet_messages.html', dialogs=dialogs, chat_msgs=chat_msgs,
                           interlocutor=interlocutor, to_id=to_id)
