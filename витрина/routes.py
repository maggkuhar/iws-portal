from flask import Blueprint, render_template
from database import get_db

bp = Blueprint('showcase', __name__, template_folder='templates')

@bp.route('/')
def index():
    db = get_db()
    products = db.execute('SELECT * FROM products WHERE in_stock = 1 ORDER BY sort_order LIMIT 8').fetchall()
    events = db.execute('''SELECT e.*, c.name as city_name FROM events e
        LEFT JOIN cities c ON e.city_id = c.id
        WHERE e.status = "открыта запись" ORDER BY e.date LIMIT 4''').fetchall()
    db.close()
    return render_template('index.html', products=products, events=events)

@bp.route('/about')
def about():
    return render_template('about.html')
