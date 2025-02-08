# Puzzlebox Dungeon Generation Algorithm
Algorithm that can create templates for dungeons like those seen in the Zelda series.
These dungeons contain state variables that the player can (and must) change as they progress from the beginning to the end.
State variables have the following properties:
- Can be reversible (like an on/off switch) or irreversible (like a key item)
- Max number of values the state variable can take (some state variables are binary, others can have more values)

## Usage

```bash
# Install requirements
python3 -m pip install pylint black

# Lint the code
python3 -m pylint main.py

# Reformat the code
python3 -m black main.py

# Run the algorithm
python3 main.py [ri][0-9]+(:[ri][0-9]+)*
```
