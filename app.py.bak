from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from database import init_db, get_db
import hashlib
import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_IMAGE = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_VIDEO = {'mp4', 'mov', 'avi', 'webm'}
ALLOWED_FILE  = ALLOWED_IMAGE | ALLOWED_VIDEO | {'pdf', 'doc', 'docx', 'zip'}
MAX_FILE_MB = 50

def allowed(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def save_upload(file, folder):
    """Сохраняет файл, возвращает имя файла или None."""
    if not file or not file.filename:
        return None
    ext = file.filename.rsplit('.', 1)[-1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(os.path.dirname(__file__), 'static', folder, name)
    file.save(path)
    return name

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'iws-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 МБ

# ─── Утилиты ────────────────────────────────────────────────────────────────

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def current_user():
    if 'user_id' not in session:
        return None
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    db.close()
    return user

@app.context_processor
def inject_user():
    user = current_user()
    unread_count = 0
    if user:
        db = get_db()
        unread_count = db.execute(
            'SELECT COUNT(*) as cnt FROM messages WHERE to_user_id = ? AND is_read = 0',
            (user['id'],)).fetchone()['cnt']
        db.close()
    return dict(user=user, unread_count=unread_count)

# ─── Блок 1: Витрина ────────────────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    products = db.execute('SELECT * FROM products WHERE in_stock = 1 ORDER BY sort_order LIMIT 8').fetchall()
    events = db.execute('''SELECT e.*, c.name as city_name FROM events e
        LEFT JOIN cities c ON e.city_id = c.id
        WHERE e.status = "открыта запись" ORDER BY e.date LIMIT 4''').fetchall()
    db.close()
    return render_template('index.html', products=products, events=events)

@app.route('/about')
def about():
    return render_template('about.html')

# ─── Блок 2: Магазин ────────────────────────────────────────────────────────

@app.route('/shop')
def shop():
    db = get_db()
    category_slug = request.args.get('category', '')
    categories = db.execute('SELECT * FROM categories ORDER BY sort_order').fetchall()
    if category_slug:
        products = db.execute('''SELECT p.*, c.name as cat_name FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE c.slug = ? AND p.in_stock = 1 ORDER BY p.sort_order''', (category_slug,)).fetchall()
    else:
        products = db.execute('''SELECT p.*, c.name as cat_name FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.in_stock = 1 ORDER BY p.sort_order''').fetchall()
    db.close()
    return render_template('shop.html', products=products, categories=categories, active_category=category_slug)

@app.route('/shop/<slug>')
def product(slug):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE slug = ?', (slug,)).fetchone()
    db.close()
    if not product:
        return redirect(url_for('shop'))
    return render_template('product.html', product=product)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/cart/add', methods=['POST'])
def cart_add():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    return jsonify({'ok': True, 'count': sum(cart.values())})

@app.route('/cart/remove', methods=['POST'])
def cart_remove():
    product_id = str(request.form.get('product_id'))
    cart = session.get('cart', {})
    cart.pop(product_id, None)
    session['cart'] = cart
    return jsonify({'ok': True, 'count': sum(cart.values())})

@app.route('/checkout')
def checkout():
    if not current_user():
        return redirect(url_for('login'))
    return render_template('checkout.html')

@app.route('/checkout', methods=['POST'])
def checkout_post():
    if not current_user():
        return redirect(url_for('login'))
    # TODO: создание заказа + оплата
    return render_template('checkout.html')

# ─── Блок 3: Личный кабинет ─────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
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
        return redirect(url_for('cabinet'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('cabinet'))
        flash('Неверный email или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/cabinet')
def cabinet():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    orders = db.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (user['id'],)).fetchall()
    db.close()
    return render_template('cabinet.html', orders=orders)

@app.route('/cabinet/profile', methods=['GET', 'POST'])
def cabinet_profile():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
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
        return redirect(url_for('cabinet_profile'))
    return render_template('cabinet_profile.html')

# ─── Блок 4: Расписание и запись ────────────────────────────────────────────

@app.route('/events')
def events():
    db = get_db()
    city_id = request.args.get('city', '')
    cities = db.execute('SELECT * FROM cities WHERE active = 1 ORDER BY name').fetchall()
    if city_id:
        evts = db.execute('''SELECT e.*, c.name as city_name FROM events e
            LEFT JOIN cities c ON e.city_id = c.id
            WHERE e.city_id = ? ORDER BY e.date''', (city_id,)).fetchall()
    else:
        evts = db.execute('''SELECT e.*, c.name as city_name FROM events e
            LEFT JOIN cities c ON e.city_id = c.id
            ORDER BY e.date''').fetchall()
    db.close()
    return render_template('events.html', events=evts, cities=cities, active_city=city_id)

@app.route('/events/<int:event_id>')
def event_detail(event_id):
    db = get_db()
    event = db.execute('''SELECT e.*, c.name as city_name FROM events e
        LEFT JOIN cities c ON e.city_id = c.id WHERE e.id = ?''', (event_id,)).fetchone()
    count = db.execute('SELECT COUNT(*) as cnt FROM event_registrations WHERE event_id = ? AND status != "отменена"',
                       (event_id,)).fetchone()['cnt']
    db.close()
    if not event:
        return redirect(url_for('events'))
    return render_template('event_detail.html', event=event, registrations_count=count)

@app.route('/events/<int:event_id>/register', methods=['POST'])
def event_register(event_id):
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    user = current_user()
    user_id = user['id'] if user else None
    db = get_db()
    db.execute('INSERT INTO event_registrations (event_id, user_id, name, phone, email) VALUES (?,?,?,?,?)',
               (event_id, user_id, name, phone, email))
    db.commit()
    db.close()
    return redirect(url_for('event_detail', event_id=event_id))

# ─── Блок 5: Сообщество ─────────────────────────────────────────────────────

@app.route('/community')
def community():
    db = get_db()
    posts = db.execute('''SELECT p.*, u.name as user_name, u.avatar as user_avatar
        FROM posts p LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC LIMIT 50''').fetchall()
    db.close()
    return render_template('community.html', posts=posts)

@app.route('/community/post', methods=['POST'])
def community_post():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    content = request.form.get('content', '').strip()
    if content:
        db = get_db()
        db.execute('INSERT INTO posts (user_id, content) VALUES (?,?)', (user['id'], content))
        db.commit()
        db.close()
    return redirect(url_for('community'))

@app.route('/cabinet/messages')
@app.route('/cabinet/messages/<int:to_id>', methods=['GET', 'POST'])
def cabinet_messages(to_id=None):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    # Список диалогов
    dialogs = db.execute('''SELECT u.id, u.name, u.avatar, u.role,
        (SELECT content FROM messages WHERE (from_user_id=u.id AND to_user_id=?) OR (from_user_id=? AND to_user_id=u.id) ORDER BY created_at DESC LIMIT 1) as last_msg,
        (SELECT created_at FROM messages WHERE (from_user_id=u.id AND to_user_id=?) OR (from_user_id=? AND to_user_id=u.id) ORDER BY created_at DESC LIMIT 1) as last_time,
        (SELECT COUNT(*) FROM messages WHERE from_user_id=u.id AND to_user_id=? AND is_read=0) as unread
        FROM users u WHERE u.id IN (
            SELECT DISTINCT CASE WHEN from_user_id=? THEN to_user_id ELSE from_user_id END
            FROM messages WHERE from_user_id=? OR to_user_id=?
        ) ORDER BY last_time DESC''',
        (user['id'], user['id'], user['id'], user['id'], user['id'], user['id'], user['id'], user['id'])).fetchall()
    # Открытый чат
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
                return redirect(url_for('cabinet_messages', to_id=to_id))
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

@app.route('/members')
def members():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    q = request.args.get('q', '').strip()
    if q:
        all_members = db.execute(
            'SELECT * FROM users WHERE id != ? AND (name LIKE ? OR city LIKE ?) ORDER BY name',
            (user['id'], f'%{q}%', f'%{q}%')).fetchall()
    else:
        all_members = db.execute(
            'SELECT * FROM users WHERE id != ? ORDER BY created_at DESC', (user['id'],)).fetchall()
    db.close()
    return render_template('members.html', all_members=all_members, q=q)

@app.route('/messages')
def messages():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
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
    db.close()
    return render_template('messages.html', dialogs=dialogs)

@app.route('/messages/<int:to_id>', methods=['GET', 'POST'])
def dialog(to_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            db.execute('INSERT INTO messages (from_user_id, to_user_id, content) VALUES (?,?,?)',
                       (user['id'], to_id, content))
            db.commit()
    db.execute('UPDATE messages SET is_read=1 WHERE from_user_id=? AND to_user_id=?', (to_id, user['id']))
    db.commit()
    msgs = db.execute('''SELECT m.*, u.name as sender_name FROM messages m
        LEFT JOIN users u ON m.from_user_id = u.id
        WHERE (from_user_id=? AND to_user_id=?) OR (from_user_id=? AND to_user_id=?)
        ORDER BY m.created_at''', (user['id'], to_id, to_id, user['id'])).fetchall()
    interlocutor = db.execute('SELECT * FROM users WHERE id=?', (to_id,)).fetchone()
    db.close()
    return render_template('dialog.html', messages=msgs, interlocutor=interlocutor)

# ─── Утилита: уровни доступа ─────────────────────────────────────────────────

ROLE_NAMES = {1: 'Участник', 2: 'Практик', 3: 'Амбассадор', 4: 'Модератор', 5: 'Администратор'}
ROLE_COLORS = {1: '#7c3aed', 2: '#0891b2', 3: '#059669', 4: '#d97706', 5: '#dc2626'}

def role_name(role): return ROLE_NAMES.get(role, 'Участник')
def role_color(role): return ROLE_COLORS.get(role, '#7c3aed')

@app.context_processor
def inject_helpers():
    return dict(role_name=role_name, role_color=role_color)

# ─── Блок 6: Профили участников ──────────────────────────────────────────────

@app.route('/profile/<int:user_id>')
def profile(user_id):
    db = get_db()
    member = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not member:
        return redirect(url_for('community'))
    posts = db.execute('''SELECT p.*, u.name as user_name FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.user_id = ? ORDER BY p.created_at DESC LIMIT 20''', (user_id,)).fetchall()
    followers = db.execute('SELECT COUNT(*) as cnt FROM subscriptions WHERE following_id = ?', (user_id,)).fetchone()['cnt']
    following = db.execute('SELECT COUNT(*) as cnt FROM subscriptions WHERE follower_id = ?', (user_id,)).fetchone()['cnt']
    achievements = db.execute('''SELECT a.* FROM achievements a
        JOIN user_achievements ua ON a.id = ua.achievement_id
        WHERE ua.user_id = ?''', (user_id,)).fetchall()
    is_following = False
    user = current_user()
    if user:
        is_following = bool(db.execute('SELECT 1 FROM subscriptions WHERE follower_id = ? AND following_id = ?',
                                       (user['id'], user_id)).fetchone())
    db.close()
    return render_template('profile.html', member=member, posts=posts,
                           followers=followers, following=following,
                           achievements=achievements, is_following=is_following)

@app.route('/profile/<int:user_id>/follow', methods=['POST'])
def follow(user_id):
    user = current_user()
    if not user or user['id'] == user_id:
        return redirect(url_for('profile', user_id=user_id))
    db = get_db()
    existing = db.execute('SELECT 1 FROM subscriptions WHERE follower_id = ? AND following_id = ?',
                          (user['id'], user_id)).fetchone()
    if existing:
        db.execute('DELETE FROM subscriptions WHERE follower_id = ? AND following_id = ?', (user['id'], user_id))
    else:
        db.execute('INSERT INTO subscriptions (follower_id, following_id) VALUES (?,?)', (user['id'], user_id))
    db.commit()
    db.close()
    return redirect(url_for('profile', user_id=user_id))

@app.route('/post/<int:post_id>/like', methods=['POST'])
def post_like(post_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    existing = db.execute('SELECT 1 FROM post_likes WHERE post_id = ? AND user_id = ?',
                          (post_id, user['id'])).fetchone()
    if existing:
        db.execute('DELETE FROM post_likes WHERE post_id = ? AND user_id = ?', (post_id, user['id']))
        db.execute('UPDATE posts SET likes = likes - 1 WHERE id = ?', (post_id,))
    else:
        db.execute('INSERT INTO post_likes (post_id, user_id) VALUES (?,?)', (post_id, user['id']))
        db.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
    db.commit()
    db.close()
    return redirect(request.referrer or url_for('community'))

# ─── Блок 7: Группы ──────────────────────────────────────────────────────────

@app.route('/groups')
def groups():
    user = current_user()
    user_role = user['role'] if user else 0
    db = get_db()
    all_groups = db.execute('SELECT * FROM groups ORDER BY min_role, name').fetchall()
    my_groups = []
    if user:
        my_groups = [g['group_id'] for g in db.execute(
            'SELECT group_id FROM group_members WHERE user_id = ?', (user['id'],)).fetchall()]
    db.close()
    return render_template('groups.html', groups=all_groups, my_groups=my_groups, user_role=user_role)

@app.route('/groups/<int:group_id>')
def group_detail(group_id):
    user = current_user()
    db = get_db()
    group = db.execute('SELECT * FROM groups WHERE id = ?', (group_id,)).fetchone()
    if not group:
        return redirect(url_for('groups'))
    if user and user['role'] < group['min_role']:
        flash('Недостаточно уровня для доступа к этой группе')
        return redirect(url_for('groups'))
    members = db.execute('''SELECT u.id, u.name, u.avatar, u.role, u.experience FROM users u
        JOIN group_members gm ON u.id = gm.user_id
        WHERE gm.group_id = ? ORDER BY gm.joined_at DESC LIMIT 50''', (group_id,)).fetchall()
    is_member = False
    if user:
        is_member = bool(db.execute('SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?',
                                    (group_id, user['id'])).fetchone())
    db.close()
    return render_template('group_detail.html', group=group, members=members, is_member=is_member)

@app.route('/groups/<int:group_id>/join', methods=['POST'])
def group_join(group_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    group = db.execute('SELECT * FROM groups WHERE id = ?', (group_id,)).fetchone()
    if group and user['role'] >= group['min_role']:
        try:
            db.execute('INSERT INTO group_members (group_id, user_id) VALUES (?,?)', (group_id, user['id']))
            db.execute('UPDATE groups SET members_count = members_count + 1 WHERE id = ?', (group_id,))
            db.commit()
        except Exception:
            db.execute('DELETE FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user['id']))
            db.execute('UPDATE groups SET members_count = members_count - 1 WHERE id = ?', (group_id,))
            db.commit()
    db.close()
    return redirect(url_for('group_detail', group_id=group_id))

# ─── Блок 8: Издательство ────────────────────────────────────────────────────

@app.route('/publishing')
def publishing():
    db = get_db()
    books = db.execute('SELECT * FROM pub_books ORDER BY sort_order, title').fetchall()
    db.close()
    return render_template('publishing.html', books=books)

@app.route('/publishing/<slug>')
def publishing_book(slug):
    db = get_db()
    book = db.execute('SELECT * FROM pub_books WHERE slug = ?', (slug,)).fetchone()
    db.close()
    if not book:
        return redirect(url_for('publishing'))
    return render_template('publishing_book.html', book=book)

# ─── Запуск ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=False)
