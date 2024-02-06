# Puzzlebox Dungeon Generation Algorithm
Algorithm that can create templates for dungeons like those seen in the Zelda series.
These dungeons contain state that the player can (and must) change as they progress from the beginning to the end.
Such state includes the following examples:
- Binary reversible: On/off switches
- Binary irreversible: Retrieving a special dungeon item
- Binary cyclic: A pair of on/off switches that each go one direction
- Numeric reversible: A switch with a set of options
- Numeric cyclic: A pair of switches that each go one direction

## Usage

```bash
# Install requirements
python3 -m pip install pylint

# Lint the code
python3 -m pylint main.py

# Run the algorithm
python3 main.py
```