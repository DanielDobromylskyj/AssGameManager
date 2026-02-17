import sqlite3
import uuid

import argon2.exceptions
from argon2 import PasswordHasher

import random

db_path = "user-info.db"

ADJECTIVES = [
    "Wobbly", "Sneaky", "Fluffy", "Grumpy", "Zippy", "Cosmic",
    "Spicy", "Sleepy", "Bouncy", "MildlyConfused", "Unhinged",
    "Questionable", "Chaotic", "Smol", "Angry"
]

NOUNS = [
    "Penguin", "Potato", "Goblin", "Banana", "Toaster", "Raccoon",
    "Wizard", "Hamster", "Noodle", "Blob", "Duck", "Mushroom"
]

def random_display_name():
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    number = random.randint(1, 99)
    return f"{adj} {noun} {number}"


class User:
    def __init__(self, user_id, user_uuid, email, display_name, admin=False):
        self.id = user_id
        self.uuid = user_uuid
        self.email = email
        self.display_name = display_name
        self.admin = admin

def update_display_name(user_id, new):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE login SET display_name = ? WHERE user_id = ?", (new, user_id))

    conn.commit()
    conn.close()



class UserManager:
    def __init__(self):
        self.path = db_path

    def create_user(self, email, password, display_name):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        ph = PasswordHasher()
        password_hash = ph.hash(password)

        cursor.execute('''INSERT INTO login (uuid, email, password, display_name) VALUES (?, ?, ?, ?)''', (
            str(uuid.uuid4()), email, password_hash, display_name
        ))

        cursor.execute('''INSERT INTO stats (user_id) VALUES (?)''', (
            cursor.lastrowid,
        ))

        conn.commit()
        conn.close()

    def get_user_by_id(self, user_id) -> User | None:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute('''SELECT email, uuid, display_name, is_host FROM login WHERE user_id = ?''', (user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return None

        return User(user_id, user[1], user[0], user[2], admin=bool(user[3]))

    def get_user_id_by_uuid(self, user_uuid) -> int | None:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute('''SELECT user_id FROM login WHERE uuid = ?''', (user_uuid,))
        user_id = cursor.fetchone()

        conn.close()

        return user_id[0] if user_id else None

    def get_all_user_data_by_id(self, user_id) -> tuple | None:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute('''SELECT * FROM login WHERE user_id = ?''', (user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return None

        return user

    def get_user(self, email) -> User | None:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute('''SELECT user_id, uuid, display_name FROM login WHERE email = ?''', (email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return None

        return User(user[0], user[1], email, user[2])

    def get_stats(self, user_id) -> dict:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute('''SELECT wins, losses, games_played, kills FROM stats WHERE user_id = ?''', (user_id,))
        data = cursor.fetchone()
        conn.close()

        return {
            "wins": data[0],
            "losses": data[1],
            "games_played": data[2],
            "kills": data[3]
       }

    def verify_user(self, email, password):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute('''SELECT password FROM login WHERE email = ?''', (email,))
        password_hash = cursor.fetchone()

        if not password_hash:
            return False

        conn.close()

        try:
            ph = PasswordHasher()
            ph.verify(password_hash[0], password)
        except argon2.exceptions.VerifyMismatchError:  # Invalid Password
            return False

        return True

    def increment_stat(self, user_id, stat):
        if stat not in ('wins', 'losses', 'games_played', 'kills'):
            raise ValueError('Invalid stat!')

        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute(f'''UPDATE stats SET {stat} = {stat} + 1 WHERE user_id = ?''', (user_id,))

        conn.commit()
        conn.close()
