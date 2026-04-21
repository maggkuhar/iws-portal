import os
from flask import Flask
from database import init_db

from витрина.routes import bp as bp_showcase
from магазин.routes import bp as bp_shop
from кабинет.routes import bp as bp_cabinet
from расписание.routes import bp as bp_schedule
from сообщество.routes import bp as bp_community

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'iws-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 МБ

@app.context_processor
def inject_user():
    from utils import current_user
    user = current_user()
    unread_count = 0
    if user:
        from database import get_db
        db = get_db()
        unread_count = db.execute(
            'SELECT COUNT(*) as cnt FROM messages WHERE to_user_id=? AND is_read=0',
            (user['id'],)).fetchone()['cnt']
        db.close()
    return dict(user=user, unread_count=unread_count)

@app.context_processor
def inject_helpers():
    ROLE_NAMES = {1: 'Участник', 2: 'Практик', 3: 'Амбассадор', 4: 'Модератор', 5: 'Администратор'}
    ROLE_COLORS = {1: '#7c3aed', 2: '#0891b2', 3: '#059669', 4: '#d97706', 5: '#dc2626'}
    def role_name(role): return ROLE_NAMES.get(role, 'Участник')
    def role_color(role): return ROLE_COLORS.get(role, '#7c3aed')
    return dict(role_name=role_name, role_color=role_color)

app.register_blueprint(bp_showcase)
app.register_blueprint(bp_shop)
app.register_blueprint(bp_cabinet)
app.register_blueprint(bp_schedule)
app.register_blueprint(bp_community)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=False)
