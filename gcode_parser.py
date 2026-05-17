
class GCodeMove:

    def __init__(self, x=None, y=None, z=None, e=None, f=None, is_extrusion=False, line_number=None):
        self.x = x
        self.y = y
        self.z = z
        self.e = e                          # Extrusion amount
        self.f = f                          # Feedrate (speed)
        self.is_extrusion = is_extrusion    # True = printing move, False = travel move
        self.line_number = line_number

    def __repr__(self):
        return (f"GCodeMove(x={self.x}, y={self.y}, z={self.z}, "
                f"e={self.e}, f={self.f}, extrusion={self.is_extrusion})")


class GCodeParser:

    def __init__(self, filepath):
        self.filepath = filepath
        self.moves = []
        self.layers = []          # List of lists, one per Z-layer
        self.errors = []
        self._parsed = False

        # Tracking current state between lines
        self._current_x = 0.0
        self._current_y = 0.0
        self._current_z = 0.0
        self._current_f = 0.0
        self._current_e = 0.0


    def parse(self):

        self.moves = []
        self.layers = []
        self.errors = []
        self._parsed = False

        try:
            with open(self.filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {self.filepath}")
        except OSError as e:
            raise OSError(f"Could not open file: {e}")

        current_layer_moves = []
        last_z = None

        for line_num, raw_line in enumerate(lines, start=1):
            line = self._strip_comment(raw_line).strip()

            if not line:
                continue

            command = self._get_command(line)

            if command in ("G0", "G1"):
                move = self._parse_move_line(line, line_num)
                if move:
                    self.moves.append(move)

                    if move.z is not None and move.z != last_z:
                        if current_layer_moves:
                            self.layers.append(current_layer_moves)
                        current_layer_moves = []
                        last_z = move.z

                    current_layer_moves.append(move)

        if current_layer_moves:
            self.layers.append(current_layer_moves)

        self._parsed = True
        return self  # Allow chaining: parser.parse().get_moves()

    def get_moves(self):

        self._check_parsed()
        return self.moves

    def get_extrusion_moves(self):

        self._check_parsed()
        return [m for m in self.moves if m.is_extrusion]

    def get_travel_moves(self):
        self._check_parsed()
        return [m for m in self.moves if not m.is_extrusion]

    def get_layers(self):
        self._check_parsed()
        return self.layers

    def get_stats(self):
        self._check_parsed()

        if not self.moves:
            return {"error": "No moves found in file."}

        xs = [m.x for m in self.moves if m.x is not None]
        ys = [m.y for m in self.moves if m.y is not None]
        zs = [m.z for m in self.moves if m.z is not None]
        feedrates = [m.f for m in self.moves if m.f is not None]

        total_distance = self._calculate_total_distance()

        return {
            "filepath": self.filepath,
            "total_moves": len(self.moves),
            "extrusion_moves": len(self.get_extrusion_moves()),
            "travel_moves": len(self.get_travel_moves()),
            "layer_count": len(self.layers),
            "x_range": (min(xs), max(xs)) if xs else (0, 0),
            "y_range": (min(ys), max(ys)) if ys else (0, 0),
            "z_range": (min(zs), max(zs)) if zs else (0, 0),
            "max_feedrate": max(feedrates) if feedrates else 0,
            "min_feedrate": min(feedrates) if feedrates else 0,
            "total_distance_mm": round(total_distance, 2),
        }

    def get_coordinates(self):
        self._check_parsed()
        xs, ys, zs = [], [], []
        cx, cy, cz = 0.0, 0.0, 0.0

        for move in self.moves:
            cx = move.x if move.x is not None else cx
            cy = move.y if move.y is not None else cy
            cz = move.z if move.z is not None else cz
            xs.append(cx)
            ys.append(cy)
            zs.append(cz)

        return xs, ys, zs
    def _strip_comment(self, line):
        idx = line.find(";")
        return line[:idx] if idx != -1 else line

    def _get_command(self, line):
        parts = line.split()
        return parts[0].upper() if parts else ""

    def _parse_move_line(self, line, line_num):
        params = {}
        parts = line.upper().split()

        for part in parts[1:]:  # Skip the command itself
            if len(part) < 2:
                continue
            key = part[0]
            try:
                value = float(part[1:])
                params[key] = value
            except ValueError:
                self.errors.append(f"Line {line_num}: could not parse '{part}'")
        x = params.get("X", None)
        y = params.get("Y", None)
        z = params.get("Z", None)
        e = params.get("E", None)
        f = params.get("F", None)

        if f is not None:
            self._current_f = f
        if e is not None:
            is_extrusion = e > self._current_e
            self._current_e = e
        else:
            is_extrusion = False
        if x is None and y is None and z is None:
            return None

        return GCodeMove(
            x=x, y=y, z=z, e=e,
            f=f if f is not None else self._current_f,
            is_extrusion=is_extrusion,
            line_number=line_num
        )

    def _calculate_total_distance(self):
        total = 0.0
        cx, cy = 0.0, 0.0

        for move in self.moves:
            nx = move.x if move.x is not None else cx
            ny = move.y if move.y is not None else cy
            total += ((nx - cx) ** 2 + (ny - cy) ** 2) ** 0.5
            cx, cy = nx, ny

        return total

    def _check_parsed(self):
        if not self._parsed:
            raise RuntimeError("Call parse() before accessing data.")
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        sample = """\
; Sample G-code test
G1 X0 Y0 Z0.2 F3000
G1 X10 Y0 E1.0 F1500
G1 X10 Y10 E2.0
G1 X0 Y10 E3.0
G1 X0 Y0 E4.0
G0 X5 Y5 Z0.4 F3000
G1 X15 Y5 E5.0 F1500
G1 X15 Y15 E6.0
"""
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".gcode", delete=False)
        tmp.write(sample)
        tmp.close()
        filepath = tmp.name
        print(f"No file given — using built-in sample: {filepath}\n")
    else:
        filepath = sys.argv[1]

    parser = GCodeParser(filepath)
    parser.parse()

    stats = parser.get_stats()
    print("=== Parse Stats ===")
    for key, val in stats.items():
        print(f"  {key}: {val}")

    print(f"\nFirst 5 moves:")
    for move in parser.get_moves()[:5]:
        print(f"  {move}")

    if len(sys.argv) < 2:
        os.unlink(filepath)
