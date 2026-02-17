import sqlite3

DB_PATH = "user-info.db"


def init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS login (
                    user_id integer PRIMARY KEY,
                    uuid text NOT NULL,
        
                    email text NOT NULL,
                    password text NOT NULL,
        
                    display_name text NOT NULL,
                    is_host boolean DEFAULT false,
                    created_at datetime DEFAULT CURRENT_TIMESTAMP
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS stats (
                    user_id integer PRIMARY KEY,
                    wins integer DEFAULT 0,
                    losses integer DEFAULT 0,
                    kills integer DEFAULT 0,
                    games_played integer DEFAULT 0
                 )''')

    conn.commit()
    conn.close()
