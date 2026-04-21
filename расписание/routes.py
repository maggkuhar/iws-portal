from flask import Blueprint, render_template, request, redirect, url_for
from database import get_db
from utils import current_user

bp = Blueprint('schedule', __name__, template_folder='templates')

@bp.route('/events')
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

@bp.route('/events/<int:event_id>')
def event_detail(event_id):
    db = get_db()
    event = db.execute('''SELECT e.*, c.name as city_name FROM events e
        LEFT JOIN cities c ON e.city_id = c.id WHERE e.id = ?''', (event_id,)).fetchone()
    count = db.execute('SELECT COUNT(*) as cnt FROM event_registrations WHERE event_id = ? AND status != "отменена"',
                       (event_id,)).fetchone()['cnt']
    db.close()
    if not event:
        return redirect(url_for('schedule.events'))
    return render_template('event_detail.html', event=event, registrations_count=count)

@bp.route('/events/<int:event_id>/register', methods=['POST'])
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
    return redirect(url_for('schedule.event_detail', event_id=event_id))
