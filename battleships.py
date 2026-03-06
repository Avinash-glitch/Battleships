import os
import random
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

ship_data = [
    ("Aircraft Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
]


class BattleshipGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Battleship Game v2")
        self.root.geometry("1120x760")

        self.game = BattleShip()
        self.player1 = None
        self.player2 = None
        self.currentPlayer = None
        self.secondPlayer = None
        self.game_running = False
        self.result_shown = False
        self.ai_target_queue = []

        self.wallpaper_image = None
        self.player_grid_canvas = None
        self.computer_grid_canvas = None
        self.message_label = None
        self.player1_status_label = None
        self.player2_status_label = None

        self.game_mode_var = tk.StringVar(value="ai")
        self.player1_name_var = tk.StringVar(value="Player 1")
        self.player2_name_var = tk.StringVar(value="Hannibal the Bot")
        self.wallpaper_path_var = tk.StringVar(value="")

        # Setup-phase drag state: tracks drag/drop and ship state before battle starts.
        self.setup_player = None
        self.setup_on_done = None
        self.setup_canvas = None
        self.setup_label = None
        self.setup_done_btn = None
        self.setup_continue_btn = None
        self.setup_drag_ship = None
        self.setup_drag_offset = (0, 0)
        self.setup_drag_moved = False
        self.setup_locked = False
        self.setup_ship_state = {}
        self.setup_board_x = 120
        self.setup_board_y = 20
        self.setup_cell = 40

        self.menu_screen()

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def menu_screen(self):
        self.game_running = False
        self.clear_root()

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        frame = ttk.Frame(self.root, padding=28)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        ttk.Label(frame, text="BATTLESHIP v2", font=("Georgia", 30, "bold"), anchor="center").grid(
            row=0, column=0, columnspan=2, pady=(0, 8), sticky="ew"
        )
        ttk.Label(
            frame,
            text="Choose mode, set names, and optional wallpaper path.",
            font=("Cambria", 12),
            anchor="center",
        ).grid(row=1, column=0, columnspan=2, pady=(0, 18), sticky="ew")

        ttk.Label(frame, text="Game Mode", font=("Cambria", 12, "bold")).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        ttk.Radiobutton(frame, text="Player vs AI", value="ai", variable=self.game_mode_var).grid(
            row=3, column=0, sticky="w"
        )
        ttk.Radiobutton(frame, text="2 Players", value="pvp", variable=self.game_mode_var).grid(
            row=3, column=1, sticky="w"
        )

        ttk.Label(frame, text="Player 1 Name").grid(row=4, column=0, sticky="w", pady=(10, 4))
        ttk.Entry(frame, textvariable=self.player1_name_var).grid(row=5, column=0, sticky="ew")
        ttk.Label(frame, text="Player 2 / Bot Name").grid(row=4, column=1, sticky="w", pady=(10, 4))
        ttk.Entry(frame, textvariable=self.player2_name_var).grid(row=5, column=1, sticky="ew")

        ttk.Label(frame, text="Wallpaper Path (optional)").grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 4))
        ttk.Entry(frame, textvariable=self.wallpaper_path_var).grid(row=7, column=0, columnspan=2, sticky="ew")

        ttk.Button(frame, text="Start Game", command=self.start_game).grid(row=8, column=0, sticky="ew", pady=(18, 0))
        ttk.Button(frame, text="Quit", command=self.root.destroy).grid(row=8, column=1, sticky="ew", pady=(18, 0))

    def add_wallpaper_slot(self, row):
        banner = tk.Frame(self.root, bg="#1b1e24", highlightthickness=0)
        banner.grid(row=row, column=0, columnspan=3, sticky="ew", padx=24, pady=(0, 8))
        banner.grid_columnconfigure(0, weight=1)

        wall_path = self.wallpaper_path_var.get().strip()
        if wall_path and os.path.exists(wall_path):
            try:
                img = tk.PhotoImage(file=wall_path)
                if img.width() > 980:
                    ratio = max(1, img.width() // 980)
                    img = img.subsample(ratio, ratio)
                self.wallpaper_image = img
                tk.Label(banner, image=self.wallpaper_image, bg="#1b1e24").grid(row=0, column=0, sticky="ew")
                return
            except tk.TclError:
                pass

        tk.Label(
            banner,
            text="Wallpaper slot: add a valid PNG/GIF path in menu.",
            font=("Cambria", 11),
            fg="#e7ddc8",
            bg="#1b1e24",
            pady=14,
        ).grid(row=0, column=0, sticky="ew")

    def start_game(self):
        self.game = BattleShip()
        self.ai_target_queue = []
        self.result_shown = False

        p1_name = self.player1_name_var.get().strip() or "Player 1"
        default_p2 = "Hannibal the Bot" if self.game_mode_var.get() == "ai" else "Player 2"
        p2_name = self.player2_name_var.get().strip() or default_p2
        vs_ai = self.game_mode_var.get() == "ai"

        self.player1 = Player(p1_name, isHuman=True)
        self.player2 = Player(p2_name, isHuman=not vs_ai)

        # In PvP, each player gets a setup screen; in PvAI, bot ships are auto-placed after P1 setup.
        if self.player2.isHuman:
            self.show_setup_screen(self.player1, lambda: self.show_setup_screen(self.player2, self.start_battle_phase))
        else:
            self.show_setup_screen(self.player1, self.after_player1_setup_vs_ai)

    def after_player1_setup_vs_ai(self):
        self.game.randomly_place_ships(self.player2, ship_data)
        self.start_battle_phase()

    # ---------------- Setup Phase: drag/rotate/place ----------------
    def show_setup_screen(self, player, on_done):
        self.clear_root()
        self.setup_player = player
        self.setup_on_done = on_done
        # Reset setup-local state every time we enter placement for a player.
        self.setup_drag_ship = None
        self.setup_locked = False
        self.setup_ship_state = {}

        self.root.grid_columnconfigure(0, weight=1)

        ttk.Label(self.root, text="Ship Placement", font=("Georgia", 26, "bold"), anchor="center").grid(
            row=0, column=0, pady=(14, 8), sticky="ew"
        )
        self.setup_label = ttk.Label(
            self.root,
            text=f"{player.name}: Drag ships from tray to grid. Click ship to rotate.",
            font=("Cambria", 12),
            anchor="center",
        )
        self.setup_label.grid(row=1, column=0, pady=(0, 8), sticky="ew")

        controls = ttk.Frame(self.root, padding=(0, 4, 0, 14))
        controls.grid(row=2, column=0, sticky="w", padx=20)
        self.setup_done_btn = ttk.Button(controls, text="Lock Placement", command=self.lock_current_setup, state="disabled")
        self.setup_done_btn.grid(row=0, column=0, padx=8)
        self.setup_continue_btn = ttk.Button(controls, text="Continue", command=self.continue_after_setup, state="disabled")
        self.setup_continue_btn.grid(row=0, column=1, padx=8)
        ttk.Button(controls, text="Auto Place", command=self.auto_place_setup_player).grid(row=0, column=2, padx=8)
        ttk.Button(controls, text="Restart Setup", command=lambda: self.show_setup_screen(player, on_done)).grid(row=0, column=3, padx=8)
        ttk.Button(controls, text="Back to Menu", command=self.menu_screen).grid(row=0, column=4, padx=8)

        self.setup_canvas = tk.Canvas(self.root, width=640, height=700, bg="#a9a9a9", highlightthickness=0)
        self.setup_canvas.grid(row=3, column=0, pady=(2, 8))

        self.draw_setup_board()
        self.init_setup_ships()

        self.setup_canvas.bind("<ButtonPress-1>", self.on_setup_press)
        self.setup_canvas.bind("<B1-Motion>", self.on_setup_drag)
        self.setup_canvas.bind("<ButtonRelease-1>", self.on_setup_release)

    def draw_setup_board(self):
        bx = self.setup_board_x
        by = self.setup_board_y
        size = self.setup_cell * 10
        self.setup_canvas.create_rectangle(bx, by, bx + size, by + size, fill="#9f9f9f", outline="#676767")
        for i in range(11):
            x = bx + i * self.setup_cell
            y = by + i * self.setup_cell
            self.setup_canvas.create_line(x, by, x, by + size, fill="#7d7d7d")
            self.setup_canvas.create_line(bx, y, bx + size, y, fill="#7d7d7d")

        self.setup_canvas.create_text(320, 448, text="Ship Tray", font=("Cambria", 14, "bold"), fill="#1f1f1f")

    def init_setup_ships(self):
        tray_y = 480
        x_positions = [40, 340]
        row_gap = 68
        for idx, (name, length) in enumerate(ship_data):
            col = idx % 2
            row = idx // 2
            x = x_positions[col]
            y = tray_y + (row * row_gap)
            width = length * self.setup_cell
            y1 = y
            y2 = y + self.setup_cell
            rect = self.setup_canvas.create_rectangle(x, y1, x + width, y2, fill="#2f6fb2", outline="#ffffff", width=2, tags=("ship", name))
            txt = self.setup_canvas.create_text(x + width / 2, y1 + self.setup_cell / 2, text=name, fill="#ffffff", font=("Cambria", 10, "bold"), tags=("ship_text", name))
            self.setup_ship_state[name] = {
                "name": name,
                "length": length,
                "orientation": 0,  # 0 horizontal, 1 vertical
                "x": x,
                "y": y1,
                "home_x": x,
                "home_y": y1,
                "rect_id": rect,
                "text_id": txt,
                "placed": False,
                "coords": [],
            }

    def find_ship_at(self, x, y):
        item = self.setup_canvas.find_closest(x, y)
        if not item:
            return None
        tags = self.setup_canvas.gettags(item[0])
        for tag in tags:
            if tag in self.setup_ship_state:
                return tag
        return None

    def on_setup_press(self, event):
        if self.setup_locked:
            return
        name = self.find_ship_at(event.x, event.y)
        if not name:
            return
        ship = self.setup_ship_state[name]
        self.setup_drag_ship = name
        self.setup_drag_moved = False
        self.setup_drag_offset = (event.x - ship["x"], event.y - ship["y"])

    def on_setup_drag(self, event):
        if self.setup_locked:
            return
        if not self.setup_drag_ship:
            return
        self.setup_drag_moved = True
        ship = self.setup_ship_state[self.setup_drag_ship]
        nx = event.x - self.setup_drag_offset[0]
        ny = event.y - self.setup_drag_offset[1]
        self.move_setup_ship(ship, nx, ny)

    def on_setup_release(self, event):
        if self.setup_locked:
            return
        if not self.setup_drag_ship:
            return
        ship = self.setup_ship_state[self.setup_drag_ship]
        self.setup_drag_ship = None

        if not self.setup_drag_moved:
            self.rotate_setup_ship(ship)
            self.refresh_setup_done_button()
            return

        # Drop logic: only keep placement if snapped to a valid non-overlapping board position.
        placed = self.try_snap_ship_to_board(ship)
        if not placed:
            if ship["placed"]:
                # keep it where it was already placed
                self.snap_ship_to_cell(ship, ship["coords"][0])
            else:
                self.move_setup_ship(ship, ship["home_x"], ship["home_y"])
        self.refresh_setup_done_button()

    def move_setup_ship(self, ship, x, y):
        ship["x"] = x
        ship["y"] = y
        w, h = self.ship_pixel_size(ship)
        self.setup_canvas.coords(ship["rect_id"], x, y, x + w, y + h)
        self.setup_canvas.coords(ship["text_id"], x + (w / 2), y + (h / 2))

    def ship_pixel_size(self, ship):
        if ship["orientation"] == 0:
            return ship["length"] * self.setup_cell, self.setup_cell
        return self.setup_cell, ship["length"] * self.setup_cell

    def rotate_setup_ship(self, ship):
        old_orientation = ship["orientation"]
        old_coords = list(ship["coords"])

        ship["orientation"] = 1 - ship["orientation"]
        # If ship is already placed on board, rotation must still satisfy bounds + overlap checks.
        if ship["placed"] and old_coords:
            start_cell = old_coords[0]
            new_coords = self.compute_ship_cells(start_cell, ship["length"], ship["orientation"])
            if not self.valid_ship_cells(ship["name"], new_coords):
                ship["orientation"] = old_orientation
                return
            ship["coords"] = new_coords
            self.snap_ship_to_cell(ship, start_cell)
            return

        self.move_setup_ship(ship, ship["x"], ship["y"])

    def try_snap_ship_to_board(self, ship):
        bx = self.setup_board_x
        by = self.setup_board_y
        x = ship["x"]
        y = ship["y"]

        col = round((x - bx) / self.setup_cell)
        row = round((y - by) / self.setup_cell)
        if not (0 <= row <= 9 and 0 <= col <= 9):
            return False

        start_cell = row * 10 + col
        coords = self.compute_ship_cells(start_cell, ship["length"], ship["orientation"])
        # Reject placements that are out-of-bounds or overlap existing placed ships.
        if not self.valid_ship_cells(ship["name"], coords):
            return False

        ship["placed"] = True
        ship["coords"] = coords
        self.snap_ship_to_cell(ship, start_cell)
        return True

    def snap_ship_to_cell(self, ship, start_cell):
        row = start_cell // 10
        col = start_cell % 10
        x = self.setup_board_x + col * self.setup_cell
        y = self.setup_board_y + row * self.setup_cell
        self.move_setup_ship(ship, x, y)

    def compute_ship_cells(self, start_cell, length, orientation):
        row = start_cell // 10
        col = start_cell % 10
        if orientation == 0:
            if col + length > 10:
                return None
            return [start_cell + i for i in range(length)]
        if row + length > 10:
            return None
        return [start_cell + (i * 10) for i in range(length)]

    def valid_ship_cells(self, ship_name, coords):
        if coords is None:
            return False
        for other_name, other in self.setup_ship_state.items():
            if other_name == ship_name or not other["placed"]:
                continue
            if set(coords).intersection(other["coords"]):
                return False
        return True

    def auto_place_setup_player(self):
        if self.setup_locked:
            return
        self.game.randomly_place_ships(self.setup_player, ship_data)
        for ship in self.setup_player.ships:
            state = self.setup_ship_state[ship.name]
            state["orientation"] = ship.orientation
            state["placed"] = True
            state["coords"] = list(ship.coordinates)
            self.snap_ship_to_cell(state, ship.coordinates[0])
        self.refresh_setup_done_button()

    def refresh_setup_done_button(self):
        all_placed = all(s["placed"] for s in self.setup_ship_state.values())
        self.setup_done_btn.config(state="normal" if all_placed else "disabled")
        if not all_placed:
            self.setup_continue_btn.config(state="disabled")

    def lock_current_setup(self):
        self.setup_player.ships = []
        for name, length in ship_data:
            state = self.setup_ship_state[name]
            if not state["placed"]:
                messagebox.showwarning("Placement Incomplete", "Please place all ships before continuing.")
                return
            ship = Ship(name, length, state["orientation"])
            ship.coordinates = list(state["coords"])
            self.setup_player.ships.append(ship)

        # Lock freezes drag/rotate and enables Continue to move to next setup/battle phase.
        self.setup_locked = True
        self.setup_done_btn.config(state="disabled")
        self.setup_continue_btn.config(state="normal")
        self.setup_label.config(text=f"{self.setup_player.name}: placement locked. Click Continue.")

    def continue_after_setup(self):
        if not self.setup_locked:
            return
        self.setup_on_done()

    # ---------------- Battle phase ----------------
    def start_battle_phase(self):
        self.clear_root()
        self.game_running = True
        self.ai_target_queue = []
        self.result_shown = False

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_columnconfigure(2, weight=1)

        ttk.Label(self.root, text="Battleship", font=("Georgia", 28, "bold"), anchor="center").grid(
            row=0, column=0, columnspan=3, pady=(14, 8), sticky="ew"
        )
        self.add_wallpaper_slot(row=1)

        ttk.Label(self.root, text=f"{self.player1.name}'s Board", font=("Cambria", 13, "bold")).grid(row=2, column=0, pady=6)
        ttk.Label(self.root, text=f"{self.player2.name}'s Board", font=("Cambria", 13, "bold")).grid(row=2, column=2, pady=6)

        self.player_grid_canvas = tk.Canvas(self.root, width=400, height=400, bg="#a9a9a9", highlightthickness=0)
        self.player_grid_canvas.grid(row=3, column=0, padx=40, pady=16)
        self.computer_grid_canvas = tk.Canvas(self.root, width=400, height=400, bg="#a9a9a9", highlightthickness=0)
        self.computer_grid_canvas.grid(row=3, column=2, padx=40, pady=16)
        self.create_grid(self.player_grid_canvas, "#7d7d7d", 400, 400)
        self.create_grid(self.computer_grid_canvas, "#7d7d7d", 400, 400)

        self.player1.player_canvas = self.player_grid_canvas
        self.player2.player_canvas = self.computer_grid_canvas

        # Ships are intentionally hidden during battle; players only see hit/miss markers.
        self.player1_status_label = ttk.Label(self.root, text="", font=("Cambria", 10), justify="left", anchor="w")
        self.player1_status_label.grid(row=4, column=0, padx=40, sticky="w")
        self.player2_status_label = ttk.Label(self.root, text="", font=("Cambria", 10), justify="left", anchor="w")
        self.player2_status_label.grid(row=4, column=2, padx=40, sticky="w")

        self.message_label = ttk.Label(self.root, text="", font=("Cambria", 12), wraplength=900, anchor="center")
        self.message_label.grid(row=5, column=0, columnspan=3, pady=8)

        controls = ttk.Frame(self.root, padding=(0, 4, 0, 14))
        controls.grid(row=6, column=0, columnspan=3)
        ttk.Button(controls, text="Restart", command=self.start_game).grid(row=0, column=0, padx=8)
        ttk.Button(controls, text="Back to Menu", command=self.menu_screen).grid(row=0, column=1, padx=8)

        self.currentPlayer = random.choice([self.player1, self.player2])
        self.secondPlayer = self.player2 if self.currentPlayer == self.player1 else self.player1
        self.update_ship_status_labels()
        self.show_message_below_grid(f"{self.currentPlayer.name} starts the game.")
        self.initiate_player_turn()

    def bind_attack_canvas(self, canvas):
        self.player_grid_canvas.unbind("<Button-1>")
        self.computer_grid_canvas.unbind("<Button-1>")
        canvas.bind("<Button-1>", self.on_click_attack)

    def initiate_player_turn(self):
        if self.game.isGameOver(self.currentPlayer, self.secondPlayer):
            if not self.result_shown:
                self.result_shown = True
                self.game_running = False
                self.show_game_result()
            return

        # Human turns wait for click input; AI turns are scheduled with after().
        if self.currentPlayer.isHuman:
            self.bind_attack_canvas(self.secondPlayer.player_canvas)
            self.show_message_below_grid(f"{self.currentPlayer.name}'s turn: fire on {self.secondPlayer.name}'s board.")
        else:
            self.player_grid_canvas.unbind("<Button-1>")
            self.computer_grid_canvas.unbind("<Button-1>")
            self.show_message_below_grid(f"{self.currentPlayer.name} is choosing a target...")
            self.root.after(700, self.game_loop_ai)

    def game_loop_ai(self):
        if not self.game_running or self.currentPlayer.isHuman:
            return

        if self.game.isGameOver(self.currentPlayer, self.secondPlayer):
            if not self.result_shown:
                self.result_shown = True
                self.game_running = False
                self.show_game_result()
            return

        shot = self.get_ai_shot()
        if shot is None:
            return

        self.currentPlayer.arrayOfShots.append(shot)
        is_hit, sunk_ship = self.game.check_hit(self.currentPlayer, self.secondPlayer, shot)
        self.place_hit_marker(self.secondPlayer.player_canvas, shot, is_hit)
        self.show_message_below_grid(self.build_shot_message(self.currentPlayer, self.secondPlayer, shot, is_hit, sunk_ship))
        self.update_ship_status_labels()

        # AI keeps shooting on hits; on miss, turn switches.
        if is_hit:
            self.add_adjacent_targets(shot)
            self.root.after(700, self.game_loop_ai)
        else:
            self.currentPlayer, self.secondPlayer = self.secondPlayer, self.currentPlayer
            self.root.after(700, self.initiate_player_turn)

    def get_ai_shot(self):
        while self.ai_target_queue:
            t = self.ai_target_queue.pop(0)
            if t not in self.currentPlayer.arrayOfShots:
                return t
        available = [cell for cell in range(100) if cell not in self.currentPlayer.arrayOfShots]
        return random.choice(available) if available else None

    def add_adjacent_targets(self, coord):
        # "Hunt-target" behavior: after a hit, prioritize orthogonal neighbor cells next.
        row = coord // 10
        col = coord % 10
        candidates = []
        if row > 0:
            candidates.append(coord - 10)
        if row < 9:
            candidates.append(coord + 10)
        if col > 0:
            candidates.append(coord - 1)
        if col < 9:
            candidates.append(coord + 1)
        for c in candidates:
            if c not in self.currentPlayer.arrayOfShots and c not in self.ai_target_queue:
                self.ai_target_queue.append(c)

    def on_click_attack(self, event):
        if not self.game_running or not self.currentPlayer.isHuman:
            return
        if event.widget != self.secondPlayer.player_canvas:
            return

        cell = self.get_cell_from_xy(event.x, event.y)
        if cell in self.currentPlayer.arrayOfShots:
            self.show_message_below_grid(f"{self.currentPlayer.name}, you already fired at {cell}.")
            return

        self.player_grid_canvas.unbind("<Button-1>")
        self.computer_grid_canvas.unbind("<Button-1>")

        self.currentPlayer.arrayOfShots.append(cell)
        is_hit, sunk_ship = self.game.check_hit(self.currentPlayer, self.secondPlayer, cell)
        self.place_hit_marker(self.secondPlayer.player_canvas, cell, is_hit)
        self.show_message_below_grid(self.build_shot_message(self.currentPlayer, self.secondPlayer, cell, is_hit, sunk_ship))
        self.update_ship_status_labels()

        if is_hit:
            self.root.after(600, self.initiate_player_turn)
        else:
            self.currentPlayer, self.secondPlayer = self.secondPlayer, self.currentPlayer
            self.root.after(600, self.initiate_player_turn)

    def place_hit_marker(self, canvas, cell, is_hit):
        self.set_coordinates(canvas, cell, "red" if is_hit else "black", 1, 1)

    def show_game_result(self):
        winner = None
        if self.currentPlayer.totalShipsSunk == len(ship_data):
            winner = self.secondPlayer.name
        elif self.secondPlayer.totalShipsSunk == len(ship_data):
            winner = self.currentPlayer.name
        messagebox.showinfo("Game Result", f"Game over! {winner} wins!" if winner else "Game over! It's a draw.")
        self.menu_screen()

    def show_message_below_grid(self, message):
        if self.message_label:
            self.message_label.config(text=message)

    def build_shot_message(self, attacker, defender, cell, is_hit, sunk_ship):
        if not is_hit:
            return f"{attacker.name} missed at {cell}."
        if sunk_ship:
            return f"{attacker.name} sank your {sunk_ship}."
        return f"{attacker.name} hit at {cell}."

    def get_ship_status_text(self, player):
        # Status panel under each board.
        lines = [f"{ship.name}: {'Sunk' if ship.is_sunk else 'Still active'}" for ship in player.ships]
        return "\n".join(lines)

    def update_ship_status_labels(self):
        if self.player1_status_label:
            self.player1_status_label.config(text=self.get_ship_status_text(self.player1))
        if self.player2_status_label:
            self.player2_status_label.config(text=self.get_ship_status_text(self.player2))

    # ---------------- drawing utils ----------------
    def get_cell_from_xy(self, x, y):
        x_cell = int(x // 40)
        y_cell = int(y // 40)
        return y_cell * 10 + x_cell

    def set_coordinates(self, canvas, value, color, orientation, ship_size):
        cell_size = 40
        x_cell = value % 10
        y_cell = value // 10
        x_start = x_cell * cell_size
        y_start = y_cell * cell_size
        if orientation == 1:
            x_end = (x_cell + 1) * cell_size
            y_end = (y_cell + ship_size) * cell_size
        else:
            x_end = (x_cell + ship_size) * cell_size
            y_end = (y_cell + 1) * cell_size
        canvas.create_rectangle(x_start, y_start, x_end, y_end, fill=color, outline="white")

    def create_grid(self, canvas, color, x, y):
        grid = 40
        for i in range(0, int(y), grid):
            canvas.create_line(0, i, x, i, fill=color)
        for i in range(0, int(x), grid):
            canvas.create_line(i, 0, i, y, fill=color)


class Player:
    def __init__(self, name, isHuman=True):
        self.name = name
        self.isHuman = isHuman
        self.totalShipsSunk = 0
        self.arrayOfHits = []
        self.ships = []
        self.arrayOfShots = []
        self.player_canvas = None


class Ship:
    def __init__(self, name, length, orientation=1):
        self.name = name
        self.length = length
        self.coordinates = []
        self.orientation = orientation  # 0 horizontal, 1 vertical
        self.is_sunk = False


class BattleShip:
    def check_hit(self, player, opponent, shot):
        is_hit = False
        sunk_ship = None
        for ship in opponent.ships:
            if shot in ship.coordinates:
                is_hit = True
                player.arrayOfHits.append(shot)
                # Return sunk ship name so UI can show "X sank your Y" messages.
                if self.ship_sunk(ship, player, opponent):
                    sunk_ship = ship.name
        return is_hit, sunk_ship

    def ship_sunk(self, opponent_ship, attacker, opponent):
        # Guard prevents counting the same ship as sunk multiple times.
        if opponent_ship.is_sunk:
            return False
        if all(cell in attacker.arrayOfHits for cell in opponent_ship.coordinates):
            opponent.totalShipsSunk += 1
            opponent_ship.is_sunk = True
            return True
        return False

    def isGameOver(self, curr_player, secondPlayer):
        return secondPlayer.totalShipsSunk == len(ship_data)

    def randomly_place_ships(self, player, data):
        used = set()
        player.ships = []
        for ship_name, ship_len in data:
            while True:
                orientation = random.choice([0, 1])
                start = random.randint(0, 99)
                if orientation == 0:
                    if (start % 10) + ship_len > 10:
                        continue
                    coords = [start + i for i in range(ship_len)]
                else:
                    if (start // 10) + ship_len > 10:
                        continue
                    coords = [start + i * 10 for i in range(ship_len)]
                if any(c in used for c in coords):
                    continue
                ship = Ship(ship_name, ship_len, orientation)
                ship.coordinates = coords
                player.ships.append(ship)
                used.update(coords)
                break


if __name__ == "__main__":
    gui = BattleshipGUI()
    gui.root.mainloop()
