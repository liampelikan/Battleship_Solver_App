import tkinter as tk
from tkinter import messagebox
import random

# App settings
GRID_SIZE = 10
SIMULATIONS = 3000

# Fleet presets
DEFAULT_SHIPS = [
    {'name': 'Carrier', 'length': 5},
    {'name': 'Battleship', 'length': 4},
    {'name': 'Cruiser', 'length': 3},
    {'name': 'Submarine', 'length': 3},
    {'name': 'Destroyer', 'length': 2}
]

SEA_BATTLE_SHIPS = [
    {'name': 'Battleship', 'length': 4},
    {'name': 'Cruiser', 'length': 3},
    {'name': 'Submarine', 'length': 3},
    {'name': 'Destroyer 1', 'length': 2},
    {'name': 'Destroyer 2', 'length': 2},
    {'name': 'Destroyer 3', 'length': 2},
    {'name': 'Dinghy 1', 'length': 1},
    {'name': 'Dinghy 2', 'length': 1},
    {'name': 'Dinghy 3', 'length': 1},
    {'name': 'Dinghy 4', 'length': 1}
]

# UI colors
COLORS = {
    'bg': '#0f172a',
    'panel': '#1e293b',
    'grid_bg': '#334155',
    'text': '#f1f5f9',
    'accent': '#38bdf8',
    'hit': '#ef4444',
    'miss': '#64748b',
    'sunk': '#020617',
    'best': '#fbbf24',
    'input_bg': '#475569', 
    'success': '#22c55e', 
    'danger': '#ef4444', 
    'imessage': '#3b82f6',
    
    'heat_low': (51, 65, 85),
    'heat_high': (16, 185, 129)
}

class BattleshipSolver:
    def __init__(self, root):
        self.root = root
        self.root.title("BATTLESHIP SOLVER")
        self.root.configure(bg=COLORS['bg'])
        self.root.resizable(True, True)
        
        # Window setup
        try:
            self.root.iconbitmap("battleship.ico")
        except:
            pass
        
        # Board state
        self.current_fleet_config = [s.copy() for s in DEFAULT_SHIPS]
        self.board_state = [['unknown' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.probs_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.fleet_status = {ship['name']: True for ship in self.current_fleet_config}
        self.confirmed_sunk_cells = set()
        
        # Widget references
        self.cell_widgets = []
        self.ship_buttons = {}
        self.fleet_container = None 
        
        self.setup_ui()
        self.run_simulation()
        self.update_move_counter()

    def setup_ui(self):
        # Main layout
        main = tk.Frame(self.root, bg=COLORS['bg'], padx=15, pady=15)
        main.pack(fill='both', expand=True)

        # Board grid
        grid_frame = tk.Frame(main, bg=COLORS['panel'], padx=8, pady=8)
        grid_frame.pack(side='left', anchor='n')

        # Grid labels
        for i in range(GRID_SIZE):
            tk.Label(grid_frame, text=str(i+1), font=('Consolas', 9, 'bold'),
                     bg=COLORS['panel'], fg=COLORS['accent'], width=4).grid(row=0, column=i+1)

        for r in range(GRID_SIZE):
            tk.Label(grid_frame, text=chr(65+r), font=('Consolas', 9, 'bold'),
                     bg=COLORS['panel'], fg=COLORS['accent'], width=3).grid(row=r+1, column=0)
            row_widgets = []
            for c in range(GRID_SIZE):
                # Cell border
                border_frame = tk.Frame(grid_frame, bg=COLORS['grid_bg'], padx=2, pady=2)
                border_frame.grid(row=r+1, column=c+1, padx=1, pady=1)
                
                # Cell button
                btn = tk.Button(border_frame, text="", font=('Arial Narrow', 10, 'bold'), 
                                width=4, height=2,
                                relief='flat', borderwidth=0, bg=COLORS['grid_bg'], fg=COLORS['text'], cursor="hand2")
                
                btn.pack(fill='both', expand=True)
                
                # Mouse actions
                btn.bind('<Button-1>', lambda e, r=r, c=c: self.handle_click(r, c, 'hit'))
                btn.bind('<Button-3>', lambda e, r=r, c=c: self.handle_click(r, c, 'miss'))
                btn.bind('<Shift-Button-1>', lambda e, r=r, c=c: self.handle_click(r, c, 'sunk'))
                
                row_widgets.append((border_frame, btn))
            self.cell_widgets.append(row_widgets)

        # Side controls
        controls = tk.Frame(main, bg=COLORS['bg'])
        controls.pack(side='left', anchor='n', padx=(10, 0), fill='y')
        
        tk.Label(controls, text="SOLVER", font=('Impact', 26),
                 bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w', pady=(0, 0))
        
        self.lbl_moves = tk.Label(controls, text="MOVES: 0", font=('Consolas', 12, 'bold'),
                                  bg=COLORS['bg'], fg=COLORS['accent'])
        self.lbl_moves.pack(anchor='w', pady=(0, 15))

        # Best target panel
        self.panel_best = tk.Frame(controls, bg=COLORS['panel'], padx=10, pady=10)
        self.panel_best.pack(fill='x', pady=(0, 15))
        
        tk.Label(self.panel_best, text="OPTIMAL TARGET", font=('Arial', 8, 'bold'),
                 bg=COLORS['panel'], fg=COLORS['text']).pack(anchor='w')
        
        self.lbl_best_coord = tk.Label(self.panel_best, text="--", font=('Arial', 28, 'bold'),
                                     bg=COLORS['panel'], fg=COLORS['best'])
        self.lbl_best_coord.pack(anchor='center', pady=2)
        
        self.lbl_best_prob = tk.Label(self.panel_best, text="0%", font=('Consolas', 11),
                                    bg=COLORS['panel'], fg='#94a3b8')
        self.lbl_best_prob.pack(anchor='center')

        # Fleet status
        fleet_header = tk.Frame(controls, bg=COLORS['bg'])
        fleet_header.pack(fill='x', pady=(5, 2))
        tk.Label(fleet_header, text="FLEET STATUS", font=('Arial', 9, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['accent']).pack(side='left')
        
        tk.Button(fleet_header, text="⚙ EDIT", font=('Arial', 7, 'bold'),
                  bg=COLORS['panel'], fg=COLORS['text'], relief='flat', 
                  command=self.open_fleet_editor).pack(side='right')

        self.fleet_container = tk.Frame(controls, bg=COLORS['bg'])
        self.fleet_container.pack(fill='x')
        self.rebuild_fleet_list()

        # Controls legend
        self.create_legend(controls)
        
        # Reset action
        tk.Button(controls, text="RESET DATA", bg=COLORS['hit'], fg='white', font=('Arial', 9, 'bold'), 
                  relief='flat', pady=8, command=self.reset_all).pack(side='bottom', fill='x', pady=(20, 0))

    def create_legend(self, parent):
        f = tk.Frame(parent, bg=COLORS['bg'], pady=10)
        f.pack(fill='x')
        
        items = [("L-Click", "Hit", COLORS['hit']), ("R-Click", "Miss", COLORS['miss']), ("Shift+Clk", "Sunk", COLORS['sunk'])]
        for key, desc, col in items:
            row = tk.Frame(f, bg=COLORS['bg'])
            row.pack(fill='x', pady=1)
            tk.Label(row, text="■", fg=col, bg=COLORS['bg'], font=('Arial', 10)).pack(side='left')
            tk.Label(row, text=f" {key}: {desc}", fg='#94a3b8', bg=COLORS['bg'], font=('Arial', 8)).pack(side='left')

    # Board input

    def handle_click(self, r, c, type_req):
        current = self.board_state[r][c]
        if type_req == 'hit': new_state = 'hit' if current != 'hit' else 'unknown'
        elif type_req == 'miss': new_state = 'miss' if current != 'miss' else 'unknown'
        elif type_req == 'sunk': new_state = 'sunk' if current != 'sunk' else 'unknown'
        self.board_state[r][c] = new_state
        
        # Keep sunk cells in sync
        if new_state == 'sunk':
            self.confirmed_sunk_cells.add((r, c))
        elif (r, c) in self.confirmed_sunk_cells:
            self.confirmed_sunk_cells.remove((r, c))
            
        self.update_move_counter()
        self.run_simulation()

    def update_move_counter(self):
        moves = sum(1 for r in range(GRID_SIZE) for c in range(GRID_SIZE) if self.board_state[r][c] != 'unknown')
        self.lbl_moves.config(text=f"MOVES: {moves}")

    def toggle_ship(self, name):
        was_alive = self.fleet_status.get(name, True)
        if was_alive:
            ship_len = next((s['length'] for s in self.current_fleet_config if s['name'] == name), 0)
            self.attempt_auto_sink(ship_len)
        self.fleet_status[name] = not was_alive
        self.update_fleet_visuals()
        self.run_simulation()

    def rebuild_fleet_list(self):
        for widget in self.fleet_container.winfo_children():
            widget.destroy()
        self.ship_buttons = {}
        for ship in self.current_fleet_config:
            frame = tk.Frame(self.fleet_container, bg=COLORS['bg'])
            frame.pack(fill='x', pady=1)
            name = ship['name']
            btn = tk.Button(frame, text=f"{name} ({ship['length']})", 
                            font=('Arial', 8), width=18, anchor='w', relief='flat', padx=5)
            btn.config(command=lambda n=name: self.toggle_ship(n))
            btn.pack(side='left')
            self.ship_buttons[name] = btn
        self.update_fleet_visuals()

    def update_fleet_visuals(self):
        for name, alive in self.fleet_status.items():
            if name in self.ship_buttons:
                btn = self.ship_buttons[name]
                if alive: btn.config(bg=COLORS['panel'], fg=COLORS['text'], text=f"✔ {name}")
                else: btn.config(bg=COLORS['bg'], fg='#475569', text=f"✕ {name} (Sunk)")

    def attempt_auto_sink(self, length):
        """Pick the best sunk segment for the selected ship length."""
        available_hits = []
        sunk_seeds = []
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                state = self.board_state[r][c]
                if state == 'sunk':
                    available_hits.append((r, c))
                    if (r, c) not in self.confirmed_sunk_cells:
                        sunk_seeds.append((r, c))
                elif state == 'hit':
                    available_hits.append((r, c))
        
        candidates = self._find_ship_candidates(available_hits, length)
        if not candidates: return False
        
        best_segment = self._score_and_select_segment(candidates, sunk_seeds, available_hits)
        if best_segment:
            for r, c in best_segment:
                self.board_state[r][c] = 'sunk'
                self.confirmed_sunk_cells.add((r, c))
            return True
        return False

    def _find_ship_candidates(self, available_hits, length):
        candidates = []
        hit_set = set(available_hits)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - length + 1):
                segment = [(r, c + i) for i in range(length)]
                if all(cell in hit_set for cell in segment): candidates.append(segment)
        for c in range(GRID_SIZE):
            for r in range(GRID_SIZE - length + 1):
                segment = [(r + i, c) for i in range(length)]
                if all(cell in hit_set for cell in segment): candidates.append(segment)
        return candidates

    def _score_and_select_segment(self, candidates, sunk_seeds, available_hits):
        if not candidates: return None
        scored = []
        for segment in candidates:
            score = 0
            seed_count = sum(1 for cell in segment if cell in sunk_seeds)
            score += seed_count * 1000
            isolation = self._calculate_isolation_score(segment, available_hits)
            score += isolation
            scored.append((score, segment))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def _calculate_isolation_score(self, segment, available_hits):
        segment_set = set(segment)
        hit_set = set(available_hits)
        extra_neighbors = 0
        for r, c in segment:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                    if (nr, nc) in hit_set and (nr, nc) not in segment_set:
                        extra_neighbors += 1
        return max(0, 100 - (extra_neighbors * 20))

    def reset_all(self):
        self.board_state = [['unknown' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.fleet_status = {ship['name']: True for ship in self.current_fleet_config}
        self.confirmed_sunk_cells = set()
        self.update_fleet_visuals()
        self.update_move_counter()
        self.run_simulation()

    # Probability solver

    def run_simulation(self):
        active_hits = []
        misses_or_sunk = set()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.board_state[r][c] == 'hit': active_hits.append((r, c))
                elif self.board_state[r][c] in ['miss', 'sunk']: misses_or_sunk.add((r, c))
        
        sim_result = self._monte_carlo_solver(active_hits, misses_or_sunk, strict_mode=True)
        if sim_result['total_weight'] == 0 and len(active_hits) > 0:
            sim_result = self._monte_carlo_solver(active_hits, misses_or_sunk, strict_mode=False)

        self.probs_grid = sim_result['probs_grid']
        self.update_visuals(sim_result['best_coord'], sim_result['max_val'])

    def _monte_carlo_solver(self, active_hits, misses_or_sunk, strict_mode):
        weighted_count_grid = [[0.0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        total_weight = 0.0
        active_ships = [s for s in self.current_fleet_config if self.fleet_status[s['name']]]
        active_hits_set = set(active_hits)

        for _ in range(SIMULATIONS):
            temp_board_coords = set()
            ship_placements = [] 
            possible = True
            random.shuffle(active_ships)
            
            for ship in active_ships:
                placed = False
                unexplained_hits = [h for h in active_hits if h not in temp_board_coords]
                can_anchor = True
                if strict_mode and ship['length'] == 1 and unexplained_hits: can_anchor = False 

                if can_anchor and unexplained_hits and random.random() < 0.85:
                    anchor = random.choice(unexplained_hits)
                    potential_starts = self._get_anchored_starts(ship['length'], anchor)
                    random.shuffle(potential_starts)
                    for r, c, orientation in potential_starts:
                        coords = self._try_place_ship(r, c, orientation, ship['length'], 
                                                      temp_board_coords, misses_or_sunk, active_hits_set, strict_mode)
                        if coords:
                            placed = True
                            ship_placements.append(coords)
                            break
                
                attempts = 0
                while not placed and attempts < 20:
                    r = random.randint(0, GRID_SIZE-1); c = random.randint(0, GRID_SIZE-1); orientation = random.choice(['H', 'V'])
                    coords = self._try_place_ship(r, c, orientation, ship['length'], 
                                                  temp_board_coords, misses_or_sunk, active_hits_set, strict_mode)
                    if coords:
                        placed = True
                        ship_placements.append(coords)
                    attempts += 1
                if not placed: possible = False; break
            
            if possible:
                if all(h in temp_board_coords for h in active_hits):
                    board_weight = 0.0
                    for s_coords in ship_placements:
                        overlap = 0
                        for sc in s_coords:
                            if sc in active_hits_set: overlap += 1
                        if overlap > 0: board_weight += (overlap ** 4) 
                        else: board_weight += 0.1
                    total_weight += board_weight
                    for r, c in temp_board_coords: weighted_count_grid[r][c] += board_weight

        final_probs = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        max_val = 0
        best_coord = None
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if total_weight > 0: final_probs[r][c] = int((weighted_count_grid[r][c] / total_weight) * 100)
                if self.board_state[r][c] == 'unknown' and final_probs[r][c] > max_val:
                    max_val = final_probs[r][c]; best_coord = (r, c)
        return {'total_weight': total_weight, 'probs_grid': final_probs, 'best_coord': best_coord, 'max_val': max_val}

    def _get_anchored_starts(self, length, anchor):
        ar, ac = anchor
        starts = []
        orientations = ['H'] if length == 1 else ['H', 'V']
        for orientation in orientations:
            if orientation == 'H':
                for i in range(length):
                    if 0 <= ac - i <= GRID_SIZE - length: starts.append((ar, ac - i, 'H'))
            else:
                for i in range(length):
                    if 0 <= ar - i <= GRID_SIZE - length: starts.append((ar - i, ac, 'V'))
        return starts

    def _try_place_ship(self, r, c, orientation, length, temp_board_coords, misses_or_sunk, active_hits_set, strict_mode):
        if orientation == 'H':
            if c + length > GRID_SIZE: return None
            coords = [(r, c+i) for i in range(length)]
        else:
            if r + length > GRID_SIZE: return None
            coords = [(r+i, c) for i in range(length)]
        for cr, cc in coords:
            if (cr, cc) in misses_or_sunk or (cr, cc) in temp_board_coords: return None
        if strict_mode:
            fully_covered = True
            for cr, cc in coords:
                if (cr, cc) not in active_hits_set: fully_covered = False; break
            if fully_covered: return None
        for coord in coords: temp_board_coords.add(coord)
        return coords

    def get_heat_color(self, percentage):
        if percentage == 0: return COLORS['grid_bg']
        p = percentage / 100.0
        c1, c2 = COLORS['heat_low'], COLORS['heat_high']
        r = int(c1[0] + (c2[0] - c1[0]) * p)
        g = int(c1[1] + (c2[1] - c1[1]) * p)
        b = int(c1[2] + (c2[2] - c1[2]) * p)
        return f'#{r:02x}{g:02x}{b:02x}'

    def update_visuals(self, best_coord, max_val):
        if best_coord:
            self.lbl_best_coord.config(text=f"{chr(65+best_coord[0])}{best_coord[1]+1}", fg=COLORS['best'])
            self.lbl_best_prob.config(text=f"Probability: {max_val}%")
        else:
            self.lbl_best_coord.config(text="--", fg=COLORS['miss'])
            self.lbl_best_prob.config(text="No targets")

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                frame, btn = self.cell_widgets[r][c]
                state = self.board_state[r][c]
                prob = self.probs_grid[r][c]
                text = ""
                bg = self.get_heat_color(prob)
                fg = 'white'
                
                border_color = COLORS['grid_bg']
                
                if state == 'hit': 
                    bg = COLORS['hit']; text = "✕"
                elif state == 'miss': 
                    bg = COLORS['panel']; fg = COLORS['miss']; text = "●"
                elif state == 'sunk': 
                    bg = COLORS['sunk']; fg = '#334155'; text = "☠"
                else:
                    if prob > 0: text = str(prob)
                    if best_coord and (r, c) == best_coord: 
                        border_color = COLORS['best']
                
                btn.config(text=text, bg=bg, fg=fg, activebackground=bg)
                frame.config(bg=border_color)

    # Fleet editor
    def open_fleet_editor(self):
        editor = tk.Toplevel(self.root)
        editor.title("Fleet Config"); editor.configure(bg=COLORS['panel']); editor.geometry("400x550")
        tk.Label(editor, text="CONFIGURE FLEET", font=('Impact', 18), bg=COLORS['panel'], fg=COLORS['text']).pack(pady=10)
        list_frame = tk.Frame(editor, bg=COLORS['panel']); list_frame.pack(fill='both', expand=True, padx=10)
        self.editor_rows = []
        def render_rows():
            for w in list_frame.winfo_children(): w.destroy()
            self.editor_rows = []
            hdr = tk.Frame(list_frame, bg=COLORS['panel']); hdr.pack(fill='x', pady=2)
            tk.Label(hdr, text="Name", bg=COLORS['panel'], fg='#94a3b8', width=18, anchor='w').pack(side='left')
            tk.Label(hdr, text="Len", bg=COLORS['panel'], fg='#94a3b8', width=5).pack(side='left')
            for ship in self.temp_fleet_config:
                row = tk.Frame(list_frame, bg=COLORS['panel']); row.pack(fill='x', pady=2)
                ent_name = tk.Entry(row, bg=COLORS['input_bg'], fg='white', relief='flat', width=18)
                ent_name.insert(0, ship['name']); ent_name.pack(side='left', padx=(0, 5))
                ent_len = tk.Entry(row, bg=COLORS['input_bg'], fg='white', relief='flat', width=5, justify='center')
                ent_len.insert(0, str(ship['length'])); ent_len.pack(side='left', padx=(0, 5))
                tk.Button(row, text="✕", bg=COLORS['danger'], fg='white', relief='flat', width=3, command=lambda s=ship: remove_ship(s)).pack(side='left')
                self.editor_rows.append((ent_name, ent_len))
        self.temp_fleet_config = [s.copy() for s in self.current_fleet_config]
        def remove_ship(s): self.temp_fleet_config.remove(s); render_rows()
        def add_ship(): self.temp_fleet_config.append({'name': 'New', 'length': 1}); render_rows()
        def reset(): self.temp_fleet_config = [s.copy() for s in DEFAULT_SHIPS]; render_rows()
        def load_sea(): self.temp_fleet_config = [s.copy() for s in SEA_BATTLE_SHIPS]; render_rows()
        def save():
            new_c = []
            try:
                for n_e, l_e in self.editor_rows:
                    n = n_e.get().strip(); l = int(l_e.get())
                    if not (1 <= l <= 10): raise ValueError("Len 1-10"); 
                    if not n: raise ValueError("No Name")
                    new_c.append({'name': n, 'length': l})
                self.current_fleet_config = new_c
                self.fleet_status = {s['name']: True for s in new_c}
                self.rebuild_fleet_list(); self.run_simulation(); editor.destroy()
            except ValueError as e: messagebox.showerror("Err", str(e))
        render_rows()
        preset = tk.Frame(editor, bg=COLORS['panel'], pady=5); preset.pack(fill='x')
        tk.Button(preset, text="DEFAULT", bg=COLORS['grid_bg'], fg='white', relief='flat', command=reset, width=10).pack(side='left', padx=10)
        tk.Button(preset, text="SEA BATTLE", bg=COLORS['imessage'], fg='white', relief='flat', command=load_sea, width=15).pack(side='left')
        foot = tk.Frame(editor, bg=COLORS['panel'], pady=10); foot.pack(fill='x', side='bottom')
        tk.Button(foot, text="+ ADD", bg=COLORS['grid_bg'], fg='white', relief='flat', command=add_ship).pack(side='left', padx=10)
        tk.Button(foot, text="SAVE", bg=COLORS['success'], fg='white', relief='flat', width=10, command=save).pack(side='right', padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipSolver(root)
    root.mainloop()