# Battleship Helper

Battleship Helper is a desktop Tkinter app that estimates the best next shot in Battleship using a Monte Carlo placement solver.

The app keeps track of your board state, simulates valid ship layouts that fit the information you have entered, and highlights the highest-probability target. Go to releases to download the windows executable.

## What the app does

- Shows a 10x10 Battleship board.
- Tracks hits, misses, and confirmed sunk cells.
- Recalculates shot probabilities after every change.
- Highlights the current best target and its estimated probability.
- Lets you enable or disable ships as they are sunk.
- Includes a fleet editor with default and Sea Battle presets.

## How to use it

1. Mark the enemy board as you play:
   - Left click: mark a hit
   - Right click: mark a miss
   - Shift + left click: mark a confirmed sunk cell
2. Read the highlighted best target panel to choose your next shot.
3. When an enemy ship is sunk, click that ship in the fleet list so the solver removes it from future simulations. It should sink the hit squares once all squares are marked as hit.



## License

This project is licensed under the MIT License. See `LICENSE`.
