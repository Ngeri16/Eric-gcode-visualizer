"""
gui.py
G-code Visualizer - Main GUI Application (Enhanced)
Arcada Programming-2 2026 — E Rit Nguyen

Features:
- Rainbow color per layer
- Animation (toolpath draws itself)
- Color by feedrate speed
- Layer-by-layer slider
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.lines import Line2D

from gcode_parser import GCodeParser


class GCodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("G-code Visualizer — Arcada 2026")
        self.root.geometry("1200x750")
        self.root.configure(bg="#1e1e2e")

        self.parser = None
        self.current_layer = tk.IntVar(value=0)
        self.color_mode = tk.StringVar(value="rainbow")
        self._anim_running = False
        self._anim_index = 0
        self._anim_moves = []
        self._anim_cx = 0.0
        self._anim_cy = 0.0
        self._anim_cz = 0.0
        self._anim_total_layers = 0
        self._anim_layer_map = {}

        self._build_ui()
    def _build_ui(self):
        sidebar = tk.Frame(self.root, bg="#2a2a3e", width=240)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0), pady=10)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="G-code Visualizer",
                 bg="#2a2a3e", fg="#cdd6f4",
                 font=("Helvetica", 13, "bold")).pack(pady=(20, 2))
        tk.Label(sidebar, text="Arcada Programming-2 2026",
                 bg="#2a2a3e", fg="#6c7086",
                 font=("Helvetica", 8)).pack(pady=(0, 15))

        tk.Button(sidebar, text="📂  Open G-code File",
                  command=self._open_file,
                  bg="#89b4fa", fg="#1e1e2e",
                  font=("Helvetica", 10, "bold"),
                  relief=tk.FLAT, cursor="hand2",
                  padx=10, pady=8).pack(fill=tk.X, padx=15)

        tk.Frame(sidebar, bg="#45475a", height=1).pack(fill=tk.X, padx=15, pady=12)
        tk.Label(sidebar, text="COLOR MODE",
                 bg="#2a2a3e", fg="#6c7086",
                 font=("Helvetica", 8, "bold")).pack(anchor=tk.W, padx=15)

        for text, val in [("🌈  Rainbow layers", "rainbow"),
                           ("⚡  Speed (feedrate)", "speed"),
                           ("🔵  Classic blue/red", "classic")]:
            tk.Radiobutton(sidebar, text=text, variable=self.color_mode, value=val,
                           command=self._replot,
                           bg="#2a2a3e", fg="#cdd6f4", selectcolor="#45475a",
                           activebackground="#2a2a3e", activeforeground="#cdd6f4",
                           font=("Helvetica", 9)).pack(anchor=tk.W, padx=20, pady=1)

        tk.Frame(sidebar, bg="#45475a", height=1).pack(fill=tk.X, padx=15, pady=12)
        tk.Label(sidebar, text="ANIMATION",
                 bg="#2a2a3e", fg="#6c7086",
                 font=("Helvetica", 8, "bold")).pack(anchor=tk.W, padx=15)

        btn_row = tk.Frame(sidebar, bg="#2a2a3e")
        btn_row.pack(fill=tk.X, padx=15, pady=5)

        self.anim_btn = tk.Button(btn_row, text="▶  Play",
                                  command=self._toggle_animation,
                                  bg="#a6e3a1", fg="#1e1e2e",
                                  font=("Helvetica", 9, "bold"),
                                  relief=tk.FLAT, cursor="hand2",
                                  padx=8, pady=5)
        self.anim_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        tk.Button(btn_row, text="⏹  Reset",
                  command=self._reset_animation,
                  bg="#f38ba8", fg="#1e1e2e",
                  font=("Helvetica", 9, "bold"),
                  relief=tk.FLAT, cursor="hand2",
                  padx=8, pady=5).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(sidebar, text="Speed:",
                 bg="#2a2a3e", fg="#6c7086",
                 font=("Helvetica", 8)).pack(anchor=tk.W, padx=15)
        self.speed_slider = tk.Scale(sidebar, from_=1, to=20,
                                     orient=tk.HORIZONTAL,
                                     bg="#2a2a3e", fg="#cdd6f4",
                                     troughcolor="#45475a", highlightthickness=0,
                                     length=200)
        self.speed_slider.set(5)
        self.speed_slider.pack(padx=15)

        tk.Frame(sidebar, bg="#45475a", height=1).pack(fill=tk.X, padx=15, pady=12)
        tk.Label(sidebar, text="FILE STATS",
                 bg="#2a2a3e", fg="#6c7086",
                 font=("Helvetica", 8, "bold")).pack(anchor=tk.W, padx=15)

        self.stats_frame = tk.Frame(sidebar, bg="#2a2a3e")
        self.stats_frame.pack(fill=tk.X, padx=15, pady=5)
        self._stat_labels = {}

        for label, key in [("File", "filepath"), ("Moves", "total_moves"),
                            ("Extrusion", "extrusion_moves"), ("Travel", "travel_moves"),
                            ("Layers", "layer_count"), ("X", "x_range"),
                            ("Y", "y_range"), ("Z", "z_range"), ("Dist", "total_distance_mm")]:
            row = tk.Frame(self.stats_frame, bg="#2a2a3e")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"{label}:", bg="#2a2a3e", fg="#6c7086",
                     font=("Helvetica", 8), width=7, anchor=tk.W).pack(side=tk.LEFT)
            v = tk.Label(row, text="—", bg="#2a2a3e", fg="#cdd6f4",
                         font=("Helvetica", 8), anchor=tk.W, wraplength=130)
            v.pack(side=tk.LEFT)
            self._stat_labels[key] = v

        tk.Frame(sidebar, bg="#45475a", height=1).pack(fill=tk.X, padx=15, pady=8)
        tk.Label(sidebar, text="LAYER VIEW  (0 = all)",
                 bg="#2a2a3e", fg="#6c7086",
                 font=("Helvetica", 8, "bold")).pack(anchor=tk.W, padx=15)

        self.layer_slider = tk.Scale(sidebar, from_=0, to=0,
                                     orient=tk.HORIZONTAL,
                                     variable=self.current_layer,
                                     command=self._on_layer_change,
                                     bg="#2a2a3e", fg="#cdd6f4",
                                     troughcolor="#45475a", highlightthickness=0,
                                     length=200)
        self.layer_slider.pack(padx=15, pady=3)

        self.layer_label = tk.Label(sidebar, text="No file loaded",
                                    bg="#2a2a3e", fg="#a6e3a1",
                                    font=("Helvetica", 9))
        self.layer_label.pack()
        plot_frame = tk.Frame(self.root, bg="#1e1e2e")
        plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.fig = plt.Figure(figsize=(9, 7), facecolor="#1e1e2e")
        self.ax = self.fig.add_subplot(111, projection='3d')
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._draw_placeholder()
    def _open_file(self):
        filepath = filedialog.askopenfilename(
            title="Select G-code file",
            filetypes=[("G-code files", "*.gcode *.nc *.txt"), ("All files", "*.*")])
        if not filepath:
            return
        try:
            self._anim_running = False
            self._anim_index = 0
            self.parser = GCodeParser(filepath)
            self.parser.parse()
            self._update_stats()
            n = len(self.parser.get_layers())
            self.layer_slider.config(to=n)
            self.current_layer.set(0)
            self.layer_label.config(text=f"Showing: All {n} layers")
            self._plot(layer=0)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{e}")
    def _update_stats(self):
        import os
        stats = self.parser.get_stats()
        for key, lbl in self._stat_labels.items():
            val = stats.get(key, "—")
            if key == "filepath":
                val = os.path.basename(str(val))
            elif key == "total_distance_mm":
                val = f"{val} mm"
            elif key in ("x_range", "y_range", "z_range"):
                val = f"{val[0]:.1f}–{val[1]:.1f} mm"
            lbl.config(text=str(val))
    def _on_layer_change(self, val):
        if self.parser is None:
            return
        self._anim_running = False
        self.anim_btn.config(text="▶  Play", bg="#a6e3a1")
        layer = int(float(val))
        n = len(self.parser.get_layers())
        self.layer_label.config(
            text=f"Showing: All {n} layers" if layer == 0 else f"Layer {layer} of {n}")
        self._plot(layer=layer)

    def _replot(self):
        if self.parser:
            self._plot(layer=self.current_layer.get())
    def _get_layer_color(self, layer_idx, total_layers):
        return plt.cm.plasma(layer_idx / max(total_layers - 1, 1))

    def _get_speed_color(self, feedrate, min_f, max_f):
        norm = (feedrate - min_f) / (max_f - min_f) if max_f != min_f else 0.5
        return plt.cm.RdYlBu_r(norm)
    def _style_axes(self):
        self.ax.set_facecolor("#1e1e2e")
        self.ax.tick_params(colors="#6c7086", labelsize=7)
        self.ax.xaxis.label.set_color("#cdd6f4")
        self.ax.yaxis.label.set_color("#cdd6f4")
        self.ax.zaxis.label.set_color("#cdd6f4")
        for pane in [self.ax.xaxis.pane, self.ax.yaxis.pane, self.ax.zaxis.pane]:
            pane.fill = False
            pane.set_edgecolor("#45475a")

    def _draw_placeholder(self):
        self.ax.clear()
        self._style_axes()
        self.ax.text(0.5, 0.5, 0.5, "Open a .gcode file to visualize",
                     transform=self.ax.transAxes, ha='center', va='center',
                     color="#6c7086", fontsize=12)
        self.ax.set_title("G-code Toolpath Visualizer", color="#cdd6f4")
        self.canvas.draw()

    def _plot(self, layer=0):
        self.ax.clear()
        self._style_axes()

        layers = self.parser.get_layers()
        mode = self.color_mode.get()

        moves_by_layer = layers if layer == 0 else ([layers[layer - 1]] if layer <= len(layers) else [])
        title_extra = f"All {len(layers)} Layers" if layer == 0 else f"Layer {layer} of {len(layers)}"

        all_moves = [m for l in moves_by_layer for m in l]
        feedrates = [m.f for m in all_moves if m.f]
        min_f = min(feedrates) if feedrates else 0
        max_f = max(feedrates) if feedrates else 1

        cx, cy, cz = 0.0, 0.0, 0.0
        total_layers = len(moves_by_layer)

        for layer_idx, layer_moves in enumerate(moves_by_layer):
            for move in layer_moves:
                nx = move.x if move.x is not None else cx
                ny = move.y if move.y is not None else cy
                nz = move.z if move.z is not None else cz

                if mode == "rainbow":
                    color = self._get_layer_color(layer_idx, total_layers) if move.is_extrusion else "#333355"
                elif mode == "speed":
                    f = move.f if move.f else min_f
                    color = self._get_speed_color(f, min_f, max_f)
                else:
                    color = "#89b4fa" if move.is_extrusion else "#f38ba8"

                lw = 1.2 if move.is_extrusion else 0.5
                alpha = 0.9 if move.is_extrusion else 0.3

                self.ax.plot([cx, nx], [cy, ny], [cz, nz],
                             color=color, linewidth=lw, alpha=alpha)
                cx, cy, cz = nx, ny, nz

        self.ax.set_xlabel("X (mm)", color="#cdd6f4")
        self.ax.set_ylabel("Y (mm)", color="#cdd6f4")
        self.ax.set_zlabel("Z (mm)", color="#cdd6f4")
        stats = self.parser.get_stats()
        self.ax.set_title(
            f"G-code Toolpath — {title_extra}\n"
            f"Moves: {stats['total_moves']} | Distance: {stats['total_distance_mm']} mm",
            color="#cdd6f4", fontsize=10)
        self.canvas.draw()
    def _toggle_animation(self):
        if self.parser is None:
            messagebox.showinfo("Info", "Open a G-code file first!")
            return
        if self._anim_running:
            self._anim_running = False
            self.anim_btn.config(text="▶  Play", bg="#a6e3a1")
        else:
            self._anim_running = True
            self.anim_btn.config(text="⏸  Pause", bg="#fab387")
            if self._anim_index == 0 or self._anim_index >= len(self._anim_moves):
                self._prepare_animation()
            self._animate_step()

    def _reset_animation(self):
        self._anim_running = False
        self.anim_btn.config(text="▶  Play", bg="#a6e3a1")
        self._anim_index = 0
        if self.parser:
            self._plot(layer=self.current_layer.get())

    def _prepare_animation(self):
        layer = self.current_layer.get()
        layers = self.parser.get_layers()
        self._anim_moves = self.parser.get_moves() if layer == 0 else (layers[layer - 1] if layer <= len(layers) else [])
        self._anim_index = 0
        self._anim_cx = 0.0
        self._anim_cy = 0.0
        self._anim_cz = 0.0
        self._anim_total_layers = len(layers)
        self._anim_layer_map = {}
        idx = 0
        for li, lmoves in enumerate(layers):
            for _ in lmoves:
                self._anim_layer_map[idx] = li
                idx += 1

        self.ax.clear()
        self._style_axes()
        stats = self.parser.get_stats()
        self.ax.set_xlim(stats["x_range"])
        self.ax.set_ylim(stats["y_range"])
        self.ax.set_zlim(stats["z_range"] if stats["z_range"][0] != stats["z_range"][1] else (0, 1))
        self.ax.set_xlabel("X (mm)", color="#cdd6f4")
        self.ax.set_ylabel("Y (mm)", color="#cdd6f4")
        self.ax.set_zlabel("Z (mm)", color="#cdd6f4")
        self.ax.set_title("Animating toolpath... ▶", color="#fab387", fontsize=10)
        self.canvas.draw()

        feedrates = [m.f for m in self._anim_moves if m.f]
        self._anim_min_f = min(feedrates) if feedrates else 0
        self._anim_max_f = max(feedrates) if feedrates else 1

    def _animate_step(self):
        if not self._anim_running:
            return
        if self._anim_index >= len(self._anim_moves):
            self._anim_running = False
            self.anim_btn.config(text="▶  Play", bg="#a6e3a1")
            self.ax.set_title("Animation complete ✓", color="#a6e3a1", fontsize=10)
            self.canvas.draw()
            return

        steps = self.speed_slider.get()
        mode = self.color_mode.get()

        for _ in range(steps):
            if self._anim_index >= len(self._anim_moves):
                break
            move = self._anim_moves[self._anim_index]
            nx = move.x if move.x is not None else self._anim_cx
            ny = move.y if move.y is not None else self._anim_cy
            nz = move.z if move.z is not None else self._anim_cz

            layer_idx = self._anim_layer_map.get(self._anim_index, 0)

            if mode == "rainbow":
                color = self._get_layer_color(layer_idx, self._anim_total_layers) if move.is_extrusion else "#333355"
            elif mode == "speed":
                f = move.f if move.f else self._anim_min_f
                color = self._get_speed_color(f, self._anim_min_f, self._anim_max_f)
            else:
                color = "#89b4fa" if move.is_extrusion else "#f38ba8"

            lw = 1.2 if move.is_extrusion else 0.5
            alpha = 0.9 if move.is_extrusion else 0.3

            self.ax.plot([self._anim_cx, nx], [self._anim_cy, ny], [self._anim_cz, nz],
                         color=color, linewidth=lw, alpha=alpha)

            self._anim_cx, self._anim_cy, self._anim_cz = nx, ny, nz
            self._anim_index += 1

        self.canvas.draw()
        self.root.after(16, self._animate_step)
if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeApp(root)
    root.mainloop()
