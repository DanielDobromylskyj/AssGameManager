import flask
from flask import request, redirect
import random
import hashlib

def hash_username(username):
    return hashlib.md5(username.encode()).hexdigest()

class App:
    def __init__(self):
        self.app = flask.Flask(__name__)
        self.app.secret_key = b'UEA-ASS-nyFo83jFIekA'

        self.unsecure_password = "UeaAss"

        routes = [
            ('/join', self.join, ["GET"]),
            ("/connect", self.connect, ["GET"]),
            ("/game/duels", self.player_duels, ["GET"]),
            ("/game/duels/status", self.duels_get_info, ["GET"]),
            ("/host/duels", self.get_host_duels, ["GET"]),
            ("/host/duels/next", self.start_next_duels, ["GET"]),
            ("/host/qr_code", self.qr_code, ["GET"]),
        ]

        for route, view_func, methods in routes:
            self.app.add_url_rule(route, methods=methods, view_func=view_func)

        self.players = {}
        self.mode = "duels"

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
        self.players[user_id] = {"playing": False, "display": username}

        return redirect(f'/game/{mode}?id={user_id}')
        #return self.send_html("public/html/connect.html")

    def _name_is_free(self, name):
        return hash_username(name) not in self.players.keys()

    def is_name_free(self):
        name = request.args.get('name')
        return {"available": self._name_is_free(name)}

    def player_duels(self):
        return self.send_html("public/html/duels/player.html")

    def duels_get_info(self):
        user_id = request.args.get('id')

        if not user_id:
            return { "is_playing": False }

        if user_id not in self.players:
            return { "is_playing": False }

        data = self.players[user_id]

        if "playing" in data:
            return {"is_playing": data["playing"]}

        return { "is_playing": False }


    def get_host_duels(self):
        return self.send_html("public/html/duels/host.html")

    def start_next_duels(self):
        if not request.args.get("pass"):
            return { "error": "bad key"}

        if request.args.get("pass") != self.unsecure_password:
            return {"error": "bad key"}

        for player_id in self.players:
            self.players[player_id]["playing"] = False

        ids = list(self.players.keys())
        p1 = random.choice(ids)
        p2 = p1

        if len(self.players) > 1:
            while p2 == p1:
                p2 = random.choice(ids)

        self.players[p1]["playing"] = True
        self.players[p2]["playing"] = True

        return {"player1": self.players[p1]["display"], "player2": self.players[p2]["display"]}

    def qr_code(self):
        return self.send_html("public/html/qrcode.html")

    def start(self):
        self.app.run(debug=True)



if __name__ == '__main__':
    app = App()
    app.start()