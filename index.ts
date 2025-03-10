/**
 * The basic unit tracking dungeon state
 */
class StateValue {
    constructor(
        public id: string,
        public value: number,
    ) {}

    toString = (): string =>
        this.id.length > 1
            ? `(${this.id[0]} >= ${this.value})`
            : `(${this.id} = ${this.value})`;
}

/**
 * Unit that tracks dungeon state possibilities
 */
class StateVar extends StateValue {
    constructor(
        id: string,
        public reversible: boolean,
        public states: number,
        value = 0,
    ) {
        super(id, value);
    }

    modified(): StateValue {
        if (this.reversible) {
            this.value =
                (Math.floor(Math.random() * (this.states - 1)) +
                    this.value +
                    1) %
                this.states;
            return new StateValue(this.id, this.value);
        }
        return new StateValue(
            this.id,
            Math.min(this.states - 1, this.value + 1),
        );
    }

    override toString = (): string =>
        `\u001b[32m${this.id}\u001b[0m (${this.reversible ? "r" : "i"}${this.states})`;
}

/**
 * Represents a single room in the dungeon
 */
class Room {
    ultimate = false;

    constructor(
        public id: number,
        public mechanism: string | null,
    ) {}

    toString = (): string =>
        `${this.id}${this.mechanism ? ` (\u001b[32m${this.mechanism[0]}\u001b[0m)` : ""}${this.ultimate ? " 💀" : ""}`;
}

/**
 * Basic implementation of a graph, used to represent a dungeon
 */
class Graph {
    edges: { src: Room; dst: Room; label: StateValue | null }[] = [];
    parents: Record<number, number> = {};
    nodes: Room[] = [];

    /**
     * Adds a conditional doorway (represented by a StateValue) between two Rooms
     */
    addEdge(src: Room, dst: Room, label: StateValue | null) {
        this.edges.push({ src, dst, label });
        this.edges.push({ src: dst, dst: src, label });
    }

    getParent(r: Room): Room | null {
        return (
            this.nodes.find((x: Room) => x.id === this.parents[r.id]) ?? null
        );
    }

    getChildren(r: Room): Room[] {
        return this.nodes.filter((x: Room) => this.parents[x.id] === r.id);
    }

    toString(): string {
        let result = `\u001b[1mRooms:\u001b[0m ${this.nodes.join(", ")}\n\u001b[1mDoorways:\u001b[0m\n`;
        for (let a = 0; a < this.edges.length; a++) {
            const e = this.edges[a];
            const before = this.edges.some(
                (x, i) =>
                    x.src.id === e.dst.id &&
                    x.dst.id === e.src.id &&
                    x.label?.id === e.label?.id &&
                    i < a,
            );
            const after = this.edges.some(
                (x, i) =>
                    x.src.id === e.dst.id &&
                    x.dst.id === e.src.id &&
                    x.label?.id === e.label?.id &&
                    i > a,
            );
            if (!before) {
                result += `  ${e.src} ${after ? "<" : "-"}-- ${e.label} --> ${e.dst}\n`;
            }
        }
        return result;
    }
}

/**
 * Returns a random element from the given array
 */
const choice = <E>(a: E[]): E => a[Math.floor(Math.random() * a.length)];

/**
 * Builds a dungeon
 */
function buildDungeon(
    paddingRooms: number,
    initialStateVars: StateVar[],
): Graph {
    const graph = new Graph();

    // Add basic nodes and edges to the graph
    graph.nodes.push(new Room(1, null));
    const numRooms =
        initialStateVars.reduce(
            (acc, v: StateVar) => acc + (v.reversible ? 1 : v.states - 1),
            0,
        ) + paddingRooms;
    for (let a = 0; a < numRooms; a++) {
        const n = new Room(a + 2, null);
        const parent = choice(graph.nodes);
        graph.addEdge(parent, n, null);
        graph.nodes.push(n);
        graph.parents[n.id] = parent.id;
    }

    // Scatter state change mechanisms amongst the nodes
    const stateVars = initialStateVars
        .map((v: StateVar) =>
            v.reversible
                ? [v]
                : Array.from(Array(v.states - 1).keys()).map(
                      (x: number) => new StateVar(v.id, false, v.states),
                  ),
        )
        .reduce((acc: StateVar[], vs: StateVar[]) => acc.concat(vs), []);
    stateVars.forEach(
        (v: StateVar) =>
            (choice(
                graph.nodes.filter((x: Room) => x.mechanism === null),
            ).mechanism = v.id),
    );

    // Reassign StateVar IDs for irreversible state so the player always
    // progresses from 1 -> ... -> N instead of a random order
    const reassignedIrreversibleValues: Record<string, number> = {};
    let irreversibleRoomsCheck: Room[] = [graph.nodes[0]];
    while (irreversibleRoomsCheck.length > 0) {
        const current = irreversibleRoomsCheck.splice(0, 1)[0];
        const mechanism = stateVars.find(
            (x: StateVar) => x.id === current.mechanism,
        );
        if (mechanism && !mechanism.reversible) {
            const value = reassignedIrreversibleValues[current.mechanism!] ?? 0;
            reassignedIrreversibleValues[current.mechanism!] = value + 1;
            mechanism.id = `${mechanism.id}${value + 1}`;
            current.mechanism = mechanism.id;
            mechanism.value = value;
        }
        irreversibleRoomsCheck = irreversibleRoomsCheck.concat(
            graph.getChildren(current),
        );
    }

    // Walk until you hit a state change mechanism, then block another path behind
    // it as a requirement. Continue this until you've traversed the entire dungeon.
    let visitedMechanisms: StateVar[] = [];
    let unvisited: Room[] = [graph.nodes[0]];
    let blocked: Room[] = [];
    const unblock = (mechanism: StateVar | null) => {
        const unblocked = choice(blocked);
        const partners = [unblocked, graph.getParent(unblocked)!];
        const modified = (mechanism ?? choice(visitedMechanisms)).modified();
        graph.edges
            .filter((x) => partners.includes(x.src) && partners.includes(x.dst))
            .forEach((x) => (x.label = modified));
        blocked.splice(blocked.indexOf(unblocked), 1);
        unvisited.push(unblocked);
    };
    while (unvisited.length > 0) {
        const current: Room = choice(unvisited);
        unvisited.splice(unvisited.indexOf(current), 1)[0];
        if (current.mechanism === null) {
            unvisited = unvisited.concat(graph.getChildren(current));
            if (unvisited.length === 0 && blocked.length > 0) {
                unblock(null);
            }
        } else {
            const currentMechanism = stateVars.find(
                (y: StateVar) => y.id === current.mechanism,
            )!;
            if (!currentMechanism.reversible) {
                visitedMechanisms = visitedMechanisms.filter(
                    (x: StateVar) => x.id[0] !== current.mechanism?.[0],
                );
            }
            visitedMechanisms.push(currentMechanism);
            blocked = blocked.concat(
                unvisited.concat(graph.getChildren(current)),
            );
            unvisited = [];
            if (blocked.length > 0) {
                unblock(currentMechanism);
            }
        }
        if (unvisited.length === 0) {
            current.ultimate = true;
        }
    }

    // Add some backwards one-way edges for early visibility
    for (let a = 0; a < Math.max(Math.ceil(numRooms / 2), 1); a++) {
        const later = choice(graph.nodes);
        let ancestor: Room | null = graph.getParent(later);
        let options: Room[] = [];
        while (ancestor !== null) {
            const older = graph.getParent(ancestor);
            options.push(ancestor);
            if (older !== null) {
                const mechanism = stateVars.find(
                    (x: StateVar) =>
                        x.id ===
                        graph.edges.find(
                            (y) =>
                                y.src === older &&
                                y.dst === ancestor &&
                                y.label !== null,
                        )?.label!.id,
                );
                if (mechanism?.reversible) {
                    options = [];
                }
            }
            ancestor = older;
        }
        if (options.length > 0) {
            graph.edges.push({ src: later, dst: choice(options), label: null });
        }
    }

    return graph;
}

/**
 * Entry point for the algorithm
 */
function main() {
    if (
        process.argv.length != 4 ||
        !process.argv[2].match(/^[0-9][0-9]?$/) ||
        !process.argv[3].match(/^([ri][0-9]+)(:([ri][0-9]+))*$/)
    ) {
        console.log(
            [
                "Usage:\n",
                "  npm start <padding rooms> <state change mechanisms>\n\n",
                "'padding' rooms should be of the form [0-9][0-9]? ",
                "'state change mechanisms' should be of the form ([ri][0-9]+)(:([ri][0-9]+))*",
            ].join(""),
        );
        process.exit(1);
    }
    if (process.argv[3].split(":").length > 26) {
        console.log(
            "\u001b[1mError:\u001b[0m too many state variables (max 26)",
        );
        process.exit(1);
    }

    // Read the input and generate our dungeon
    const stateVars = process.argv[3]
        .split(":")
        .map(
            (x: string, i: number) =>
                new StateVar(
                    String.fromCharCode(65 + i),
                    x[0] === "r",
                    parseInt(x.substring(1)),
                ),
        );
    const dungeon = buildDungeon(parseInt(process.argv[2]), stateVars);

    // Print the results
    console.log(
        `\u001b[1mState Variables:\u001b[0m ${stateVars.map((x) => x.toString()).join(", ")}`,
    );
    console.log(dungeon.toString());
}

main();
