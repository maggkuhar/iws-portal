from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
from utils import current_user

bp = Blueprint('community', __name__, template_folder='templates')

@bp.route('/community')
def community():
    db = get_db()
    posts = db.execute('''SELECT p.*, u.name as user_name, u.avatar as user_avatar
        FROM posts p LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC LIMIT 50''').fetchall()
    db.close()
    return render_template('community.html', posts=posts)

@bp.route('/community/post', methods=['POST'])
def community_post():
    user = current_user()
    if not user:
        return redirect(url_for('cabinet.login'))
    content = request.form.get('content', '').strip()
    if content:
        db = get_db()
        db.execute('INSERT INTO posts (user_id, content) VALUES (?,?)', (user['id'], content))
        db.commit()
        db.close()
    return redirect(url_for('community.community'))

@bp.route('/members')
def members():
    user = current_user()
    if not user:
        return redirect(url_for('cabinet.login'))
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

@bp.route('/profile/<int:user_id>')
def profile(user_id):
    db = get_db()
    member = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not member:
        return redirect(url_for('community.community'))
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

@bp.route('/profile/<int:user_id>/follow', methods=['POST'])
def follow(user_id):
    user = current_user()
    if not user or user['id'] == user_id:
        return redirect(url_for('community.profile', user_id=user_id))
    db = get_db()
    existing = db.execute('SELECT 1 FROM subscriptions WHERE follower_id = ? AND following_id = ?',
                          (user['id'], user_id)).fetchone()
    if existing:
        db.execute('DELETE FROM subscriptions WHERE follower_id = ? AND following_id = ?', (user['id'], user_id))
    else:
        db.execute('INSERT INTO subscriptions (follower_id, following_id) VALUES (?,?)', (user['id'], user_id))
    db.commit()
    db.close()
    return redirect(url_for('community.profile', user_id=user_id))

@bp.route('/post/<int:post_id>/like', methods=['POST'])
def post_like(post_id):
    user = current_user()
    if not user:
        return redirect(url_for('cabinet.login'))
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
    return redirect(request.referrer or url_for('community.community'))

@bp.route('/groups')
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

@bp.route('/groups/<int:group_id>')
def group_detail(group_id):
    user = current_user()
    db = get_db()
    group = db.execute('SELECT * FROM groups WHERE id = ?', (group_id,)).fetchone()
    if not group:
        return redirect(url_for('community.groups'))
    if user and user['role'] < group['min_role']:
        flash('Недостаточно уровня для доступа к этой группе')
        return redirect(url_for('community.groups'))
    members = db.execute('''SELECT u.id, u.name, u.avatar, u.role, u.experience FROM users u
        JOIN group_members gm ON u.id = gm.user_id
        WHERE gm.group_id = ? ORDER BY gm.joined_at DESC LIMIT 50''', (group_id,)).fetchall()
    is_member = False
    if user:
        is_member = bool(db.execute('SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?',
                                    (group_id, user['id'])).fetchone())
    db.close()
    return render_template('group_detail.html', group=group, members=members, is_member=is_member)

@bp.route('/groups/<int:group_id>/join', methods=['POST'])
def group_join(group_id):
    user = current_user()
    if not user:
        return redirect(url_for('cabinet.login'))
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
    return redirect(url_for('community.group_detail', group_id=group_id))

@bp.route('/messages')
def messages():
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
    db.close()
    return render_template('messages.html', dialogs=dialogs)

@bp.route('/messages/<int:to_id>', methods=['GET', 'POST'])
def dialog(to_id):
    user = current_user()
    if not user:
        return redirect(url_for('cabinet.login'))
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
