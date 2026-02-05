import random

from flask import request


class Game:
    def __init__(self, app):
        self.app = app
        self.send_html = app.send_html
        self.players = app.players
        self.auth = app.validate_password

        self.game_methods = [
            ("duels", self.player_duels),
            ("duels/status", self.duels_get_info),
        ]

        self.host_methods = [
            # Path, Func, Is_Protected
            ("duels", self.get_host_duels, False),
            ("duels/next", self.start_next_duels, True)
        ]

    def player_duels(self):
        return self.send_html("public/html/duels/player.html")

    def duels_get_info(self):
        user_id = request.args.get('id')

        if not user_id:
            return { "error": "Bad User ID"}

        if user_id not in self.players:
            return { "error": "Not Logged In"}

        data = self.players[user_id]

        if "playing" in data:
            return {"is_playing": data["playing"]}

        return { "is_playing": False }

    def get_host_duels(self):
        return self.send_html("public/html/duels/host.html")

    def start_next_duels(self):
        """

        if not request.args.get("pass"):
            return { "error": "Bad Passkey"}

        if request.args.get("pass") != self.unsecure_password:
            return {"error": "Bad Passkey"}

        if self.mode != "duels":
            return { "error": "Game mode 'Duels' is not currently active"}


        """

        for player_id in self.players:
            self.players[player_id]["playing"] = False

        ids = list(self.players.keys())

        if len(ids) == 0:
            return { "error": "No Players Connected"}

        p1 = random.choice(ids)
        p2 = p1

        if len(self.players) > 1:
            while p2 == p1:
                p2 = random.choice(ids)

        self.players[p1]["playing"] = True
        self.players[p2]["playing"] = True

        return {"player1": self.players[p1]["display"], "player2": self.players[p2]["display"]}
