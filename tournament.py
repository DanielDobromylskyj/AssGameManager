import random
import time
from flask import redirect


class Game:
    def __init__(self, app):
        self.app = app
        self.send_html = app.send_html
        self.players = app.players
        self.auth = app.validate_password

        self.game_methods = [
            ("duels_t", self.player_duels),
        ]

        self.host_methods = [
            # Path, Func, Is_Protected
            ("duels_t", self.get_host_duels, False),
            ("duels_t/bracket", self.get_brackets, True),
            ("duels_t/players", self.get_players, True),
        ]

        self.bracket_layout = []

        # Testing Only!!!
        self.add_random_players()
        self.generate_tournament()

    def add_random_players(self):
        print("DEBUG FUNCTION CALLED")

        self.players = {
            "1": {"playing": False, "display": "Ben Dover", "last_ping": time.time()},
            "2": {"playing": False, "display": "Luka Mycleavage", "last_ping": time.time()},
            "3": {"playing": False, "display": "Mike Ox Long", "last_ping": time.time()},
            "4": {"playing": False, "display": "Dixie Normus", "last_ping": time.time()},
            "5": {"playing": False, "display": "Ivana Sukyuov", "last_ping": time.time()},
            "6": {"playing": False, "display": "Ivana Humpalot", "last_ping": time.time()},
            "7": {"playing": False, "display": "Fook Yu", "last_ping": time.time()},
            "8": {"playing": False, "display": "Dixie Rect", "last_ping": time.time()},
            "9": {"playing": False, "display": "Hugh Janus", "last_ping": time.time()},
        }

    def get_players(self):
        return self.players

    def generate_tournament(self):
        # Seed the game
        players = [*self.players]  # Copy array
        random.shuffle(players)


        slots = [
            (players[(game_index*2)], players[(game_index*2) + 1])
            for game_index in range(len(players) // 2)
        ]

        if len(players) % 2 != 0:
            slots.append((players[-1],))

        self.bracket_layout = [
            {
                "slots": slots,
                "connections": []
            }
        ]

        while len(slots) > 1:
            new_slots = [
                (None, None)
                for game_index in range(len(slots) // 2)
            ]

            if len(slots) % 2 != 0:
                new_slots.append((None,))

            self.bracket_layout.append({
                "slots": new_slots,
                "connections": []  # todo
            })

            slots = new_slots



    def player_duels(self):
        return self.send_html("public/html/duels_t/player.html")

    def get_host_duels(self):
        return self.send_html("public/html/duels_t/host.html")

    def get_brackets(self):
        return self.bracket_layout
