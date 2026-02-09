import time

import flask
from flask import request, redirect, send_file, abort
import random
import hashlib
import os

import game_duels
import tournament


def hash_username(username):
    return hashlib.md5(username.encode()).hexdigest()

def sha256(data):  # Yes, I know this is VERY bad practice.
    return hashlib.sha256(data.encode()).hexdigest()


class App:
    def __init__(self):
        self.app = flask.Flask(__name__)
        self.app.secret_key = b'UEA-ASS-nyFo83jFIekA'

        self.unsecure_password = "34707c3f40dfa20c3902b807b627d420d6d474d9d98066ba637953d1cfd6b914"

        routes = [
            ("/public/<path:path>", self.get_public, ["GET"]),
            ('/join', self.join, ["GET"]),
            ("/connect", self.connect, ["GET"]),

            ("/game/<path:path>", self.on_game_call, ["GET"]),
            ("/host/<path:path>", self.on_host_call, ["GET"]),
            ("/host-validate", self.host_validate_password, ["GET"]),

            ("/host/qr_code", self.qr_code, ["GET"]),
        ]

        for route, view_func, methods in routes:
            self.app.add_url_rule(route, methods=methods, view_func=view_func)


        self.players = {}

        self.game_methods = {}
        self.host_methods = {}

        self.games = {
            "duels": game_duels.Game(self),
            "duels_t": tournament.Game(self),
        }

        self.__reload_game_methods()

        self.mode = "duels"

        self.mimes = {
            "html": "text/html",
            "css": "text/css",
            "js": "application/javascript",
            "png": "image/png",
            "jpg": "image/jpeg",
            "gif": "image/gif",
            "json": "application/json"
        }

    def __reload_game_methods(self):
        for game_name in self.games:
            game = self.games[game_name]

            for path, func, protected in game.host_methods:
                if path not in self.host_methods:
                    self.host_methods[path] = (func, protected)
                else:
                    raise ValueError(f"Host method {path} already exists")

            for path, func in game.game_methods:
                if path not in self.game_methods:
                    self.game_methods[path] = func
                else:
                    raise ValueError(f"Game method {path} already exists")

    def get_public(self, path):
        path = os.path.join("public", path)

        if os.path.exists(path):
            ending = path.split(".")[-1]

            mimeType = None
            if ending in self.mimes:
                mimeType = self.mimes[ending]

            return send_file(path, mimeType)

        abort(404)

    def send_html(self, path):
        with open(path, 'r', encoding='ascii') as f:
            return f.read()

    def join(self):
        return self.send_html("public/html/set_username.html")

    def connect(self):
        username = request.args.get("username")
        mode = request.args.get("mode")

        if not self._name_is_free(username):
            return redirect(f'/join?mode={mode}')

        if mode != self.mode:
            return redirect(f'/join?mode={self.mode}')

        user_id = hash_username(username)
        self.players[user_id] = {"playing": False, "display": username, "last_ping": time.time()}

        return redirect(f'/game/{mode}?id={user_id}')
        #return self.send_html("public/html/connect.html")

    def on_game_call(self, path):
        user_id = request.args.get("id")

        if not user_id:
            abort(400)

        self.players[user_id]["last_ping"] = time.time()

        if path not in self.game_methods:
            abort(404)

        return self.game_methods[path]()

    def on_host_call(self, path):
        if path not in self.host_methods:
            abort(404)

        password = request.args.get("pass")

        if not self.validate_password(password) and self.host_methods[path][1]:
            abort(400)

        self.cleanup()

        return self.host_methods[path][0]()

    def host_validate_password(self):
        return {"valid": self.validate_password(request.args.get("pass"))}

    def validate_password(self, password):
        try:
            return sha256(password) == self.unsecure_password
        except AttributeError:
            return False

    def cleanup(self):
        drop_time = time.time() - (5 * 60)  # secs (5 mins)

        for player_id in self.players:
            if self.players[player_id]["last_ping"] < drop_time:
                self.players.pop(player_id)

    def _name_is_free(self, name):
        return hash_username(name) not in self.players.keys()

    def is_name_free(self):
        name = request.args.get('name')
        return {"available": self._name_is_free(name)}

    def qr_code(self):
        return self.send_html("public/html/qrcode.html")

    def start(self):
        self.app.run(port=8000, debug=True)



if __name__ == '__main__':
    app = App()
    app.start()
