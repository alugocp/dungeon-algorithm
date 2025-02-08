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

## Explanation
### State Graph
This is a graph that represents every possible global state given the input state variables.
Reversible state variables cause bi-directional edges between nodes.

### State Walk
The algorithm comes up with a solution to the dungeon before generating it.
This solution is a random path through the state graph.

### Dungeon Enclaves
An enclave is a set of mutually-accessible dungeon rooms.
You don't need any keys or special state or anything to move between two rooms in the same enclave.
There is one enclave for each `state variable change mechanism`, and one additional final enclave for the dungeon boss.
The `state variable change mechanisms` allow you to change the dungeon state and move between enclaves using `conditional doorways`.
Each enclave is only accessible for some subset of nodes in the state walk, which prevents you from taking shortcuts to the final state.
`Conditional doorways` connect enclaves together and are only open while the dungeon is in certain states.

### Simplified Passages
Some `conditional doorways` are open for a set of states that can be simplified into a single rule (e.g. when the first state variable is off).
This section of the output displays a map of `conditional doorways` into their simplified rules.
