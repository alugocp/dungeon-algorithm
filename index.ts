/**
 * The basic unit tracking dungeon state
 */
class StateValue {
    constructor(
        public id: string,
        public value: number,
    ) {}

    toString = (): string => `(${this.id} = ${this.value})`;
}

/**
 * Unit that tracks dungeon state possibilities
 */
class StateVar {
    constructor(
        public id: string,
        public reversible: boolean,
        public states: number,
    ) {}

    toString = (): string =>
        `\u001b[32m${this.id}\u001b[0m (${this.reversible ? "r" : "i"}${this.states})`;
}

/**
 * Represents a single room in the dungeon
 */
class Room {
    constructor(
        public id: number,
        public mechanism: string | null,
    ) {}

    toString = (): string =>
        this.mechanism
            ? `${this.id} (\u001b[32m${this.mechanism}\u001b[0m)`
            : `${this.id}`;
}

/**
 * Basic implementation of a graph, used to represent a dungeon
 */
class Graph {
    edges: { src: Room; dst: Room; label: StateValue | null }[] = [];
    nodes: Room[] = [];

    /**
     * Adds a conditional doorway (represented by a StateValue) between two Rooms
     */
    addEdge(src: Room, dst: Room, label: StateValue | null) {
        this.edges.push({ src, dst, label });
        this.edges.push({ src: dst, dst: src, label });
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
            if (!before) {
                result += `  ${e.src} <-- ${e.label} --> ${e.dst}\n`;
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
function buildDungeon(paddingRooms: number, stateVars: StateVar[]): Graph {
    const graph = new Graph();
    graph.nodes.push(new Room(1, null));
    for (let a = 0; a < stateVars.length + paddingRooms - 1; a++) {
        const n = new Room(a + 2, null);
        graph.addEdge(choice(graph.nodes), n, null);
        graph.nodes.push(n);
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
                "'padding' rooms should be of the form [0-9][0-9]?",
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
