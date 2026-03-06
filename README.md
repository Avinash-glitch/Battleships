# Battleships

A Python Battleship game with:
- Player vs AI and 2 Player modes
- Drag-and-drop ship placement
- Click-to-rotate ships during setup
- Smart AI targeting (tries adjacent cells after a hit)
- Live ship status (Sunk / Still active)

----------------------------------------
Requirements
----------------------------------------
- Python 3.8+
- Tkinter (usually included with Python)

To verify Tkinter:
python -m tkinter

----------------------------------------
How to Run
----------------------------------------
From terminal:
python "E:\course_material\software and systems\battleship\battleships.py"

----------------------------------------
Game Setup
----------------------------------------
1. Launch the game.
2. Choose mode:
   - Player vs AI
   - 2 Players
3. Enter player names.
4. (Optional) Provide wallpaper path (PNG/GIF recommended).
5. Click Start Game.

----------------------------------------
Ship Placement
----------------------------------------
1. Drag ships from tray to the board.
2. Click a ship to rotate it.
3. Ships must be:
   - Inside board bounds
   - Not overlapping any other ship
4. When all ships are placed:
   - Click Lock Placement
   - Click Continue

In Player vs AI:
- After Player 1 continues, AI ships are auto-placed.

In 2 Player mode:
- Player 1 places and continues first.
- Then Player 2 gets their own placement screen.

----------------------------------------
Battle Phase
----------------------------------------
- Ships are hidden once battle starts.
- Click on opponent board to fire.
- Red = Hit, Black = Miss.
- Hit messages include sink notifications:
  Example: "Alice sank your Destroyer."

Below each board:
- Each ship is listed with status:
  - Sunk
  - Still active

----------------------------------------
Controls
----------------------------------------
Setup screen:
- Lock Placement
- Continue
- Auto Place
- Restart Setup
- Back to Menu

Battle screen:
- Restart
- Back to Menu

----------------------------------------
Notes for GitHub
----------------------------------------
If uploading to GitHub, you can rename this file to:
README.md

Then GitHub will render it automatically on the repository home page.

