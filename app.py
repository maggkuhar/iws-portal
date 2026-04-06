from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from database import init_db, get_db
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'iws-secret-key-change-in-production')

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
    return dict(user=current_user())

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
        db = get_db()
        db.execute('UPDATE users SET name=?, phone=?, city=? WHERE id=?',
                   (name, phone, city, user['id']))
        db.commit()
        db.close()
        return redirect(url_for('cabinet'))
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

@app.route('/messages')
def messages():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    dialogs = db.execute('''SELECT u.id, u.name, u.avatar,
        (SELECT content FROM messages WHERE (from_user_id=u.id AND to_user_id=?) OR (from_user_id=? AND to_user_id=u.id) ORDER BY created_at DESC LIMIT 1) as last_msg,
        (SELECT COUNT(*) FROM messages WHERE from_user_id=u.id AND to_user_id=? AND is_read=0) as unread
        FROM users u WHERE u.id IN (
            SELECT DISTINCT CASE WHEN from_user_id=? THEN to_user_id ELSE from_user_id END
            FROM messages WHERE from_user_id=? OR to_user_id=?
        )''', (user['id'], user['id'], user['id'], user['id'], user['id'], user['id'])).fetchall()
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

# ─── Запуск ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=False)
