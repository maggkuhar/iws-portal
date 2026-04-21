from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from database import get_db
from utils import current_user

bp = Blueprint('shop', __name__, template_folder='templates')

@bp.route('/shop')
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

@bp.route('/shop/<slug>')
def product(slug):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE slug = ?', (slug,)).fetchone()
    db.close()
    if not product:
        return redirect(url_for('shop.shop'))
    return render_template('product.html', product=product)

@bp.route('/cart')
def cart():
    return render_template('cart.html')

@bp.route('/cart/add', methods=['POST'])
def cart_add():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    return jsonify({'ok': True, 'count': sum(cart.values())})

@bp.route('/cart/remove', methods=['POST'])
def cart_remove():
    product_id = str(request.form.get('product_id'))
    cart = session.get('cart', {})
    cart.pop(product_id, None)
    session['cart'] = cart
    return jsonify({'ok': True, 'count': sum(cart.values())})

@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not current_user():
        return redirect(url_for('cabinet.login'))
    # TODO: создание заказа + оплата
    return render_template('checkout.html')

@bp.route('/publishing')
def publishing():
    db = get_db()
    books = db.execute('SELECT * FROM pub_books ORDER BY sort_order, title').fetchall()
    db.close()
    return render_template('publishing.html', books=books)

@bp.route('/publishing/<slug>')
def publishing_book(slug):
    db = get_db()
    book = db.execute('SELECT * FROM pub_books WHERE slug = ?', (slug,)).fetchone()
    db.close()
    if not book:
        return redirect(url_for('shop.publishing'))
    return render_template('publishing_book.html', book=book)
