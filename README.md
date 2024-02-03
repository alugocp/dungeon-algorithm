# Puzzlebox Dungeon Generation Algorithm
Algorithm that can create dungeons like those seen in the Zelda series.
These dungeons contain state that the player can (and must) change as they progress from the beginning to the end.
Such state includes reversible switches, tertiary and higher state (i.e. the water level in OoT's Water Temple), and generic locked doors with keys.

## Usage

```bash
# Install requirements
python3 -m pip install pylint

# Lint the code
python3 -m pylint main.py

# Run the algorithm
python3 main.py
```