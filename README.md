# G-code Visualizer with Python GUI
*Arcada University of Applied Sciences — Programming-2 2026* 
**E Rit Nguyen**

## Description
A Python desktop application that reads and visualises G-code files used in 3D printing and CNC machining. The toolpath is rendered in an interactive 3D plot inside a GUI.

## Features
- Parse G0/G1 movement commands from any .gcode file
- 3D toolpath visualisation with matplotlib
- Colour modes: Rainbow (per layer), Speed (feedrate), Classic
- Layer-by-layer slider view
- Animation — watch the toolpath draw itself in real time
- File statistics (total moves, layers, distance, XYZ range)

## Files
- `gcode_parser.py` — G-code parser class (OOP)
- `visualiser.py` — Standalone 3D visualizer
- `gui.py` — Main GUI application (tkinter + matplotlib)

## How to Run
1. Install dependencies:
   pip install matplotlib
2. Run the app:
   python gui.py

## Concepts Applied
- Object-Oriented Programming (OOP)
- File I/O and data parsing
- Data visualisation with matplotlib
- GUI development with tkinter
