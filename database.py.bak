import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'iws.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    # Пользователи
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password_hash TEXT NOT NULL,
        avatar TEXT,
        city TEXT,
        bio TEXT,
        role INTEGER DEFAULT 1,
        experience INTEGER DEFAULT 0,
        referral_code TEXT UNIQUE,
        referred_by INTEGER,
        telegram_id INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    )''')

    # Категории товаров
    conn.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        sort_order INTEGER DEFAULT 0
    )''')

    # Товары
    conn.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        old_price REAL,
        image TEXT,
        type TEXT DEFAULT 'physical',
        in_stock INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )''')

    # Заказы
    conn.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        status TEXT DEFAULT 'новый',
        total REAL NOT NULL,
        delivery_address TEXT,
        delivery_city TEXT,
        payment_method TEXT,
        payment_status TEXT DEFAULT 'не оплачен',
        comment TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Позиции заказа
    conn.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    # Города и представительства
    conn.execute('''CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        country TEXT DEFAULT 'Россия',
        coordinator_name TEXT,
        coordinator_contact TEXT,
        active INTEGER DEFAULT 1
    )''')

    # Мероприятия (офлайн игры)
    conn.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        time TEXT,
        address TEXT,
        max_participants INTEGER,
        price REAL DEFAULT 0,
        status TEXT DEFAULT 'открыта запись',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (city_id) REFERENCES cities(id)
    )''')

    # Записи на мероприятия
    conn.execute('''CREATE TABLE IF NOT EXISTS event_registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        user_id INTEGER,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        status TEXT DEFAULT 'ожидает',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (event_id) REFERENCES events(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Посты сообщества
    conn.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        image TEXT,
        likes INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Комментарии
    conn.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (post_id) REFERENCES posts(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Сообщения (переписка)
    conn.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user_id INTEGER NOT NULL,
        to_user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (from_user_id) REFERENCES users(id),
        FOREIGN KEY (to_user_id) REFERENCES users(id)
    )''')

    # Подписки (follow)
    conn.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        follower_id INTEGER NOT NULL,
        following_id INTEGER NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(follower_id, following_id),
        FOREIGN KEY (follower_id) REFERENCES users(id),
        FOREIGN KEY (following_id) REFERENCES users(id)
    )''')

    # Лайки постов
    conn.execute('''CREATE TABLE IF NOT EXISTS post_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(post_id, user_id),
        FOREIGN KEY (post_id) REFERENCES posts(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Группы сообщества
    conn.execute('''CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        image TEXT,
        min_role INTEGER DEFAULT 1,
        members_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )''')

    # Участники групп
    conn.execute('''CREATE TABLE IF NOT EXISTS group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        joined_at TEXT DEFAULT (datetime('now')),
        UNIQUE(group_id, user_id),
        FOREIGN KEY (group_id) REFERENCES groups(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Достижения
    conn.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        icon TEXT,
        experience_reward INTEGER DEFAULT 0
    )''')

    # Достижения пользователей
    conn.execute('''CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        achievement_id INTEGER NOT NULL,
        earned_at TEXT DEFAULT (datetime('now')),
        UNIQUE(user_id, achievement_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (achievement_id) REFERENCES achievements(id)
    )''')

    # Издательство — книги
    conn.execute('''CREATE TABLE IF NOT EXISTS pub_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        author TEXT,
        description TEXT,
        cover TEXT,
        pages INTEGER,
        year INTEGER,
        product_id INTEGER,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    # Миграция: добавить новые колонки если БД старая
    for col, definition in [('bio', 'TEXT'), ('role', 'INTEGER DEFAULT 1'), ('experience', 'INTEGER DEFAULT 0')]:
        try:
            conn.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')
        except Exception:
            pass

    try:
        conn.execute('ALTER TABLE messages ADD COLUMN attachment TEXT')
        conn.execute('ALTER TABLE messages ADD COLUMN attachment_type TEXT')
    except Exception:
        pass

    # Начальные группы
    conn.execute("INSERT OR IGNORE INTO groups (name, slug, description, min_role) VALUES ('Женский клуб', 'women', 'Пространство для женщин', 1)")
    conn.execute("INSERT OR IGNORE INTO groups (name, slug, description, min_role) VALUES ('Дневник снов', 'dreams', 'Расшифровка и обсуждение снов', 1)")
    conn.execute("INSERT OR IGNORE INTO groups (name, slug, description, min_role) VALUES ('МАК практики', 'mak', 'Работа с МАК картами', 2)")
    conn.execute("INSERT OR IGNORE INTO groups (name, slug, description, min_role) VALUES ('Амбассадоры', 'ambassadors', 'Представители IWS в городах', 3)")

    # Начальные достижения
    conn.execute("INSERT OR IGNORE INTO achievements (id, name, description, icon, experience_reward) VALUES (1, 'Первый шаг', 'Зарегистрировался на портале', '🌱', 10)")
    conn.execute("INSERT OR IGNORE INTO achievements (id, name, description, icon, experience_reward) VALUES (2, 'Первый пост', 'Опубликовал первый пост', '✍️', 20)")
    conn.execute("INSERT OR IGNORE INTO achievements (id, name, description, icon, experience_reward) VALUES (3, 'Участник события', 'Записался на мероприятие', '🎯', 30)")
    conn.execute("INSERT OR IGNORE INTO achievements (id, name, description, icon, experience_reward) VALUES (4, 'Покупатель', 'Сделал первый заказ', '🛍️', 25)")
    conn.execute("INSERT OR IGNORE INTO achievements (id, name, description, icon, experience_reward) VALUES (5, 'Практик', 'Набрал 100 очков опыта', '⭐', 50)")

    # Начальные категории
    conn.execute("INSERT OR IGNORE INTO categories (name, slug, sort_order) VALUES ('Дневники', 'diaries', 1)")
    conn.execute("INSERT OR IGNORE INTO categories (name, slug, sort_order) VALUES ('МАК карты', 'mak', 2)")
    conn.execute("INSERT OR IGNORE INTO categories (name, slug, sort_order) VALUES ('Книги', 'books', 3)")
    conn.execute("INSERT OR IGNORE INTO categories (name, slug, sort_order) VALUES ('Игры', 'games', 4)")
    conn.execute("INSERT OR IGNORE INTO categories (name, slug, sort_order) VALUES ('Мерч', 'merch', 5)")
    conn.execute("INSERT OR IGNORE INTO categories (name, slug, sort_order) VALUES ('Онлайн', 'online', 6)")

    conn.commit()
    conn.close()
