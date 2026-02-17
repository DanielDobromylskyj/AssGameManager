import random

from flask import request, abort, redirect
from flask_login import current_user


class Game:
    def __init__(self, app):
        self.app = app
        self.active_players = {}

        self.brackets = []
        self.active_bracket = 0
        self.active_duel = 0

        self.game_over = False

        self.game_methods = {
            "": self.get_player_page,
            "status": self.get_player_stats,
            "join": self.join_session
        }

        self.host_methods = {
            "": self.get_host_page,
            "bracket": self.get_bracket,
            "players": self.get_players,
            "on_win": self.on_duel_end,
            "current": self.get_current_duel,
            "start": self.generate_tournament,
            "reset": self.reset,
            "join": self.join_qr
        }

    # Fetch Methods
    def get_host_page(self):
        return self.app.send_file('public/html/games/host_tournament.html')

    def get_player_page(self):
        return self.app.send_file('public/html/games/player_tournament.html')

    def get_bracket(self):
        return self.brackets

    def get_players(self):
        return self.active_players

    def get_player_stats(self):
        if not current_user.is_authenticated:
            return {"error": "Not logged in"}

        if current_user.uuid not in self.active_players:
            return {"error": "You are not a part of this game"}

        if self.game_over:
            return {"error": "Game Over"}

        return {"is_playing": self.active_players[current_user.uuid]["playing"]}

    def join_qr(self):
        return self.app.send_file('public/html/games/qr_tournament.html')

    # Game Logic
    def generate_tournament(self):
        players = [*self.active_players]  # Copy array
        random.shuffle(players)

        slots = [
            {
                "p1": players[(game_index * 2)],
                "p2": players[(game_index * 2) + 1],
                "mode": "unactive", "next": None
            } for game_index in range(len(players) // 2)
        ]

        if len(players) % 2 != 0:
            slots.append({
                "p1": players[-1], "p2": False, "mode": "solo", "next": None
            })

        self.brackets = [slots]

        while len(slots) > 1:
            new_slots = [
                {"p1": None, "p2": None, "mode": "unactive", "next": None}
                for game_index in range(len(slots) // 2)
            ]

            if len(slots) % 2 != 0:
                new_slots.append({"p1": None, "p2": False, "mode": "solo", "next": None})

            self.brackets.append(new_slots)

            slots = new_slots

        # Create connections
        for bracket in self.brackets[:-1]:
            total_bracket_players = sum([2 if duel["p1"] and duel["p2"] else 1 for duel in bracket])

            if (total_bracket_players % 2) == 0:
                for i, duel in enumerate(bracket):
                    duel["next"] = i

            else:  # Odd means we need a parse though -> More complicated
                # Force move the single
                bracket[-1]["next"] = 0

                # Re-assign the rest
                pointer = 1
                for duel in bracket:
                    if duel["next"] is None:
                        duel["next"] = pointer
                        pointer += 1

        # Update To Ensure everything starts correctly
        self.reset_players()
        self.update_active_players()
        return {}

    def update_tournament(self):
        for i, bracket in enumerate(self.brackets):
            if i == len(self.brackets) - 1:
                continue

            next_bracket = self.brackets[i+1]
            for duel in bracket:
                index = duel["next"] // 2
                player = "p1" if duel["next"] % 2 == 0 else "p2"

                if duel["mode"].startswith("won"):
                    winner = duel["p1"] if duel["mode"] == "won_p1" else duel["p2"]
                    next_bracket[index][player] = winner

                if duel["mode"] == "solo":
                    next_bracket[index][player] = duel["p1"]

    def get_current_duel(self):
        if self.game_over:
            return {}

        return self.brackets[self.active_bracket][self.active_duel]

    def continue_to_next_duel(self):
        if self.game_over:
            return

        self.active_duel += 1

        if self.active_duel == len(self.brackets):
            self.active_duel = 0
            self.active_bracket += 1

        if self.active_bracket == len(self.brackets):
            self.game_over = True

        if not self.game_over:
            self.reset_players()
            self.update_active_players()

    def update_active_players(self):
        new_duel = self.get_current_duel()

        if new_duel["mode"] != "done":
            if new_duel["p1"]:
                self.active_players[new_duel["p1"]]["playing"] = True

            if new_duel["p2"]:
                self.active_players[new_duel["p2"]]["playing"] = True

    def on_duel_end(self):
        winner = request.args.get("winner")

        duel = self.get_current_duel()

        self.reset_players()

        self.app.increment_player_stat(duel["p1"], "games_played")
        self.app.increment_player_stat(duel["p2"], "games_played")

        if winner == duel["p1"]:
            duel["mode"] = "won_p1"

            self.app.increment_player_stat(duel["p1"], "kills")
            self.app.increment_player_stat(duel["p1"], "wins")
            self.app.increment_player_stat(duel["p2"], "losses")

        elif winner == duel["p2"]:
            duel["mode"] = "won_p2"

            self.app.increment_player_stat(duel["p2"], "kills")
            self.app.increment_player_stat(duel["p2"], "wins")
            self.app.increment_player_stat(duel["p1"], "losses")

        else:
            return abort(400)

        self.continue_to_next_duel()
        return {}

    def reset_players(self):
        for uid in self.active_players:
            self.active_players[uid]["playing"] = False

    def reset(self):
        self.active_players = {}
        self.game_over = False

        self.active_duel = 0
        self.active_bracket = 0

        return {}

    def add_player(self, player):
        self.active_players[player.uuid] = {"playing": False, "display": player.display}

    def join_session(self):
        self.add_player(current_user)
        return redirect("/game/tournament/")

    def start_game(self):
        self.generate_tournament()
        return {}


