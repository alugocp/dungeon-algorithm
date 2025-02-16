# Puzzlebox Dungeon Generation Algorithm
Algorithm that can create templates for dungeons like those seen in the Zelda series.
These dungeons contain state variables that the player can (and must) change as they progress from the beginning to the end.
State variables have the following properties:
- Can be reversible (like an on/off switch) or irreversible (like a key item)
- Max number of values the state variable can take (irreversible variables are always binary)

## Usage

```bash
# Install (development) requirements
git config core.hooksPath .husky
npm install

# Reformat the code
npx prettier -w index.js

# Run the algorithm
npm start [ri][0-9]+(:[ri][0-9]+)*
```

## Explanation
### Enclaves
An enclave is a set of mutually-accessible dungeon rooms.
You don't need any keys or special state or anything to move between two rooms in the same enclave.
There is one enclave for each state variable.
An enclave allows you to change its state variable in the dungeon state and move between enclaves using doorways.

### Doorways
Doorways connect enclaves together and are only open while the dungeon is in a satisfying state.
The player will have to modify state variables in enclaves in order to open these doorways and progress through the dungeon.

### Unused enclaves
Sometimes state variables are left unrepresented in doorways.
These are tracked in the program and logged at the end.
The designer can place extra enclaves using these state variables in doorways.
Extra enclaves may include a boss battle or bonus room.