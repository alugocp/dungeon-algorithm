# Puzzlebox Dungeon Generation Algorithm
Algorithm that can create templates for dungeons like those seen in the Zelda series.
These dungeons contain state that the player can (and must) change as they progress from the beginning to the end.
Such state includes the following examples:
- Binary reversible: On/off switches
- Binary irreversible: Retrieving a special dungeon item

## Usage

```bash
# Install requirements
python3 -m pip install pylint black

# Lint the code
python3 -m pylint main.py

# Reformat the code
python3 -m black main.py

# Run the algorithm
python3 main.py example.json
```

The script expects some configuration JSON file in order to work.
You can use the `example.json` provided in this repository or create your own.
Each config file has the following layout:
- `width`: Width of the generated rectangular dungeon
- `height`: Height of the generated rectangular dungeon
- `state`: A list of the variables that modify traversal through your dungeon (switches, dungeon items, etc)
- `total_final_state`: A list of one integer for every item in `state`, where each integer is no greater than the `value` field in its corresponding `state` entry

Occasionally when running the script you'll see an error like `Did not find path to a final total state node`.
This is a random failure because I didn't want to add retry logic, just rerun the script.

## Explanation
### Terms
- `State` is some variable (binary or numerical) that affects your progression through the dungeon
- `Total state` is the sum of all states in the dungeon
- `Value` is one of several possibilities that a state can be in at a given time
- `State type` describes how a state can change with respect to the player's position in the dungeon
- `Enclave` is a set of rooms that are all mutually navigable no matter the dungeon's total state

### Algorithm

#### Set up the state graph
- Read input config to get the requested state types and final total state
- Calculate all possible total states and create nodes for them
- Use the state types to add edges to the state graph
- Make a random walk from the initial total state node (where every state has value 0) to the final total state
- Every edge in the state graph represents a `state change`, where one value in the total state changes by plus or minus 1 (or some arbitrary value for reversible state types)

#### Generate dungeon layout
- This side of the algorithm is mostly optional, except for the last part
- Create a new network called the room graph, which represents the physical dungeon itself 
- Create W x H rooms (nodes) and connect them at random into an enclave for each unique state change from the state graph + 1 (the extra enclave is for the boss room)
- Assign each enclave (minus the last one) to one of the unique state changes (some room in this enclave will facilitate that state change, i.e. contain a dungeon item or switch)
- At each state node in the state graph, create a passage between enclaves represented by its edges (the passage is conditional upon the total state of the node)

#### Output
The script outputs a description of the generated state and room graphs.
It also outputs a list of enclaves that the room graph nodes are grouped into, as well as the conditional passages between those enclaves.
It is up to you to decide which rooms contain the state change mechanisms (switches, dungeon items, etc) or the conditional passages between enclaves.
You can also decide to ignore the exact rooms assigned to each enclave and design the physical layout of the dungeon yourself.
This algorithm mainly helps organize the dungeon state and generates a traversal that does not cause softlocks.
