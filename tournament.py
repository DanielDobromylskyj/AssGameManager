import random
import time
from flask import request, abort


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
            ("duels_t/on_win", self.on_duel_end, True),
            ("duels_t/current", self.get_current_duel, True),
            ("duels_t/start", self.generate_tournament, True),
        ]

        self.bracket_layout = []

        self.current_bracket = 0
        self.current_duel = 0

    def get_players(self):
        return self.players

    def generate_tournament(self):
        # Reset
        self.current_bracket = 0
        self.current_duel = 0

        # Seed the game
        players = [*self.players]  # Copy array
        random.shuffle(players)


        slots = [
            {
                "p1": players[(game_index*2)],
                "p2": players[(game_index*2) + 1],
                "mode": "unactive", "next": None
            } for game_index in range(len(players) // 2)
        ]

        if len(players) % 2 != 0:
            slots.append({
                "p1": players[-1], "p2": False, "mode": "solo", "next": None
            })

        self.bracket_layout = [slots]

        while len(slots) > 1:
            new_slots = [
                { "p1": None, "p2": None, "mode": "unactive", "next": None }
                for game_index in range(len(slots) // 2)
            ]

            if len(slots) % 2 != 0:
                new_slots.append({ "p1": None, "p2": False, "mode": "solo", "next": None })

            self.bracket_layout.append(new_slots)

            slots = new_slots

        # Create connections
        for bracket in self.bracket_layout[:-1]:
            total_bracket_players = sum([ 2 if duel["p1"] and duel["p2"] else 1 for duel in bracket ])

            if (total_bracket_players % 2) == 0:
                for i, duel in enumerate(bracket):
                    duel["next"] = i

            else: # Odd means we need a parse though -> More complicated
                # Force move the single
                bracket[-1]["next"] = 0

                # Re-assign the rest
                pointer = 1
                for duel in bracket:
                    if duel["next"] is None:
                        duel["next"] = pointer
                        pointer += 1

        self.update_tournament()

        duel = self.get_current_duel()
        if duel["mode"] != "done":
            if duel["p1"]:
                self.players[duel["p1"]]["playing"] = True

            if duel["p2"]:
                self.players[duel["p2"]]["playing"] = True

        return {}

    def update_tournament(self):
        for i, bracket in enumerate(self.bracket_layout):
            if i == len(self.bracket_layout) - 1:
                continue

            next_bracket = self.bracket_layout[i+1]
            for duel in bracket:
                index = duel["next"] // 2
                player = "p1" if duel["next"] % 2 == 0 else "p2"
                if duel["mode"].startswith("won"):
                    winner = duel["p1"] if duel["mode"] == "won_p1" else duel["p2"]
                    next_bracket[index][player] = winner

                if duel["mode"] == "solo":
                    next_bracket[index][player] = duel["p1"]


    def player_duels(self):
        return self.send_html("public/html/duels_t/player.html")

    def get_host_duels(self):
        return self.send_html("public/html/duels_t/host.html")

    def get_brackets(self):
        return self.bracket_layout

    def proceed_to_next_duel(self):
        self.update_tournament()

        current_bracket = self.bracket_layout[self.current_bracket]

        self.current_duel += 1
        if self.current_duel == len(current_bracket):
            self.current_duel = 0
            self.current_bracket += 1

            if self.current_bracket == len(self.bracket_layout):
                return None  # Game Complete

        if self.get_current_duel()["mode"] == "solo":
            return self.proceed_to_next_duel()


        duel = self.get_current_duel()

        if duel["mode"] != "done":
            if duel["p1"]:
                self.players[duel["p1"]]["playing"] = True

            if duel["p2"]:
                self.players[duel["p2"]]["playing"] = True

        return None

    def on_duel_end(self):
        winner = request.args.get("winner")

        duel = self.get_current_duel()

        for player in self.players:
            self.players[player]["playing"] = False

        if winner == duel["p1"]:
            duel["mode"] = "won_p1"

        elif winner == duel["p2"]:
            duel["mode"] = "won_p2"

        else:
            return abort(400)

        self.proceed_to_next_duel()
        return {}

    def get_current_duel(self):
        if self.current_bracket == len(self.bracket_layout):
            return {"mode": "done"}

        print(self.current_duel)

        return self.bracket_layout[self.current_bracket][self.current_duel]
