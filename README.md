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
npm start [0-9][0-9]? ([ri][0-9]+)(:([ri][0-9]+))*
```

## Explanation
### State Variables
These keep track of changes the player can make while they progress the dungeon.
These changes are necessary to proceed - they can be keys, switches, levers or other power-ups.
State can be reversible (r) or irreversible (i).
Reversible state are switches, irreversible would be keys, upgrades or other accumulative concepts.
Some rooms are labelled with a state variables, that means that you can change the given variable in that room.

### Doorways
Doorways connect rooms together and are only open while the given state condition holds true.
The player will have to modify state variables in rooms in order to open these doorways and progress through the dungeon.
A doorway labelled with null means that it is always open.
A doorway with only one arrow denotes a one-way passage.
Those are so that players can get a sneak preview of later rooms, and are optional for the dungeon design.

### Skull emoji
The skull emoji denotes the "final" room of the dungeon.
It could be a boss room or just whatever you want to put in it.
