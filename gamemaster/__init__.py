import mimetypes

import flask
import flask_login
from flask import request
from flask_login import UserMixin, login_required, current_user
import secrets
import os
import uuid

from .db_manager import init as init_db
from .user_manager import UserManager, update_display_name

from .tournaments import Game as TournamentGame

class User(UserMixin):
    def __init__(self, user_id, email, display, is_admin=False, uid=None):
        self.id = str(user_id)          # MUST be a str
        self.email = email
        self.display = display
        self.is_admin = is_admin
        self.uuid = str(uuid.uuid4()) if uid is None else uid




class WebServer:
    def __init__(self):
        init_db()

        self.app = flask.Flask(__name__)
        self.app.config['SECRET_KEY'] = secrets.token_urlsafe(32)

        self.user_manager = UserManager()

        self.login_manager = flask_login.LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = 'login'

        self.login_manager.user_loader(self.load_user)

        self.players = {}

        self.game_methods = {}
        self.host_methods = {}

        self.games = {
            "tournament": TournamentGame(self),
        }

        routes = [
            ('/public/<path:path>', self.public, ["GET"]),
            ('/login', self.login, ["GET", "POST"]),
            ('/signup', self.signup, ["GET", "POST"]),
            ('/', self.account, ["GET"]),
            ('/account-info', self.accountInfo, ["GET"]),
            ('/account/set_username', self.update_username, ["GET"]),
            ('/host/<path:path>', self.host_call, ["GET"]),
            ('/game/<path:path>', self.game_call, ["GET"]),
        ]

        for route, view_func, methods in routes:
            self.app.add_url_rule(route, view_func=view_func, methods=methods)

    @login_required
    def host_call(self, path):
        if not current_user.is_admin:
            return flask.abort(403)

        return self.on_call(path, True)

    @login_required
    def game_call(self, path):
        return self.on_call(path, False)

    def on_call(self, path: str, is_host: bool):
        segments = path.split("/")

        if len(segments) == 0:
            return flask.abort(404)

        if len(segments) == 1:
            segments.append('')

        game_mode = segments[0]
        game_path = "/".join(segments[1:])

        if game_mode not in self.games:
            return flask.abort(404)

        game = self.games[game_mode]

        paths = game.host_methods if is_host else game.game_methods

        if game_path not in paths:
            return flask.abort(404)

        return paths[game_path]()


    @staticmethod
    def get_mime(extension):
        return mimetypes.guess_type(extension)[0]

    def send_file(self, path):
        return flask.send_file(
            str(os.path.abspath(path)),
            self.get_mime(path.split(".")[-1])
        )

    def public(self, path):
        path = os.path.join('public', path)

        if not os.path.exists(path):
            return flask.abort(404)

        return self.send_file(path)

    def load_user(self, user_id):
        info = self.user_manager.get_user_by_id(user_id)

        if not info:
            return None

        return User(info.id, info.email, info.display_name, is_admin=info.admin, uid=info.uuid)


    def login(self):
        if flask.request.method == 'POST':
            email = flask.request.form['email']
            password = flask.request.form['password']

            if self.user_manager.verify_user(email, password):
                info = self.user_manager.get_user(email)
                user = User(info.id, info.email, info.display_name, is_admin=info.admin, uid=info.uuid)
                flask_login.login_user(user)

                target = request.args.get('next')

                if not target:
                    return flask.redirect('/')

                return flask.redirect(target)

            return "Invalid credentials", 401

        return self.send_file("public/html/login.html")

    def signup(self):
        if flask.request.method == 'POST':
            email = flask.request.form['email']
            password = flask.request.form['password']

            if self.user_manager.get_user(email):
                return "Email in use", 401

            self.user_manager.create_user(email, password, user_manager.random_display_name())

            # Login User (It just makes the site smoother not having to enter details twice)
            info = self.user_manager.get_user(email)
            user = User(info.id, info.email, info.display_name, is_admin=info.admin, uid=info.uuid)
            flask_login.login_user(user)
            return flask.redirect('/')

        return self.send_file("public/html/signup.html")


    @login_required
    def account(self):
        return self.send_file("public/html/account.html")

    @login_required
    def accountInfo(self):
        info = self.user_manager.get_all_user_data_by_id(current_user.id)

        return {
            "display": info[4],
            "email": info[2],
            "uuid": info[1],
            "joined": info[6],
            "badges": ["Game Master"] if info[5] else [],
            "stats": self.user_manager.get_stats(current_user.id)
        }

    @login_required
    def update_username(self):
        update_display_name(current_user.id, request.args.get('name'))
        return {}

    def increment_player_stat(self, user_uuid, stat):
        self.user_manager.increment_stat(self.user_manager.get_user_id_by_uuid(user_uuid), stat)


    def start(self):
        self.app.run(port=8000, debug=True)
