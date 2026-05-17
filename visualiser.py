import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from gcode_parser import GCodeParser


class GCodeVisualizer:
    def __init__(self, filepath):
        self.filepath = filepath
        self.parser = GCodeParser(filepath)
        self.parser.parse()

    def plot(self):
        moves = self.parser.get_moves()
        stats = self.parser.get_stats()

        if not moves:
            print("No moves found in file!")
            return

        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')
        cx, cy, cz = 0.0, 0.0, 0.0

        for move in moves:
            nx = move.x if move.x is not None else cx
            ny = move.y if move.y is not None else cy
            nz = move.z if move.z is not None else cz

            color = 'blue' if move.is_extrusion else 'red'
            linewidth = 1.0 if move.is_extrusion else 0.5
            alpha = 0.8 if move.is_extrusion else 0.3

            ax.plot([cx, nx], [cy, ny], [cz, nz],
                    color=color, linewidth=linewidth, alpha=alpha)

            cx, cy, cz = nx, ny, nz
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_zlabel('Z (mm)')
        ax.set_title(f'G-code Toolpath Visualizer\n'
                     f'Layers: {stats["layer_count"]} | '
                     f'Moves: {stats["total_moves"]} | '
                     f'Distance: {stats["total_distance_mm"]} mm')
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='blue', linewidth=2, label='Extrusion (printing)'),
            Line2D([0], [0], color='red',  linewidth=1, label='Travel (no print)', alpha=0.5),
        ]
        ax.legend(handles=legend_elements, loc='upper left')

        plt.tight_layout()
        plt.show()
if __name__ == "__main__":
    import sys
    import tempfile
    import os

    if len(sys.argv) >= 2:
        filepath = sys.argv[1]
    else:
        sample = """\
; Sample G-code — a simple square spiral
G1 X0 Y0 Z0.2 F3000
G1 X50 Y0 E5.0 F1500
G1 X50 Y50 E10.0
G1 X0 Y50 E15.0
G1 X0 Y0 E20.0
G0 X5 Y5 Z0.4 F3000
G1 X45 Y5 E25.0 F1500
G1 X45 Y45 E30.0
G1 X5 Y45 E35.0
G1 X5 Y5 E40.0
G0 X10 Y10 Z0.6 F3000
G1 X40 Y10 E45.0 F1500
G1 X40 Y40 E50.0
G1 X10 Y40 E55.0
G1 X10 Y10 E60.0
"""
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".gcode", delete=False)
        tmp.write(sample)
        tmp.close()
        filepath = tmp.name
        print(f"No file given — using built-in sample\n")

    vis = GCodeVisualizer(filepath)
    vis.plot()
    if len(sys.argv) < 2:
        os.unlink(filepath)
