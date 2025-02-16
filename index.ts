/**
 * The basic unit tracking dungeon state
 */
type StateVar = {
    id: string;
    states: number;
    value: number;
    reversible: boolean;
};

/**
 * A collection of StateVars
 */
class State {
    readonly vars: StateVar[];

    constructor(...vars: StateVar[]) {
        let a = 0;
        const idsToIndices: Record<string, number> = {};
        this.vars = vars.map((x: StateVar) => ({ ...x }));
        while (a < this.vars.length) {
            const index = idsToIndices[this.vars[a].id];
            if (index === undefined) {
                idsToIndices[this.vars[a].id] = a++;
            } else {
                this.vars[index].value = this.vars[a].value;
                this.vars.splice(a, 1);
            }
        }
    }

    toString = (): string =>
        `\u001b[32m${this.vars.reduce((acc, v) => `${acc}${v.id}${v.value}`, "")}\u001b[0m`;

    /**
     * Returns a subset of this State with StateVars that have been (or can be) changed
     */
    relevant = (): State =>
        new State(...this.vars.filter((x) => x.reversible || x.value > 0));

    /**
     * Returns true if this State's StateVars satisfy the values provided by the given State
     */
    satisfies = (s: State): boolean =>
        s.vars.reduce(
            (acc, x) =>
                acc && this.vars.find((y) => y.id === x.id)?.value === x.value,
            true,
        );

    /**
     * Returns true if this State is logically equal to the given State
     */
    equals = (s: State): boolean =>
        this.vars.length === s.vars.length &&
        this.vars.reduce(
            (acc: boolean, x: StateVar) =>
                acc && s.vars.some((y) => y.id === x.id && y.value === x.value),
            true,
        );
}

/**
 * Represents a set of rooms in the dungeon that are mutually accessible
 */
class Enclave {
    constructor(public readonly mechanism: StateVar) {}

    toString = (): string =>
        `\u001b[32m${this.mechanism.id}\u001b[0m(\u001b[2m${this.mechanism.reversible ? `r${this.mechanism.states}` : "b"}\u001b[0m)`;

    /**
     * Returns true if this Enclave can still change the dungeon state
     */
    mutable = (): boolean =>
        this.mechanism.reversible || this.mechanism.value === 0;

    /**
     * Returns true if this Enclave is logically equal to the given Enclave
     */
    equals = (s: Enclave): boolean => this.mechanism.id === s.mechanism.id;

    /**
     * Returns a version of this Enclave's StateVar after it has been modified
     */
    activated(currentState: State): StateVar {
        let value = Math.floor(Math.random() * (this.mechanism.states - 1)) + 1;
        if (this.mechanism.reversible) {
            const current = currentState.vars.find(
                (x) => x.id === this.mechanism.id,
            )!.value;
            value = Math.floor(Math.random() * (this.mechanism.states - 1));
            if (value >= current) {
                value++;
            }
        }
        return {
            ...this.mechanism,
            value,
        };
    }
}

/**
 * Convenience type of both an Enclave and a State
 */
type EnclaveAndState = {
    enclave: Enclave;
    state: State;
};

/**
 * Basic implementation of a graph, used to represent a dungeon
 */
class Graph {
    edges: { src: Enclave; dst: Enclave; label: State }[] = [];
    nodes: Enclave[] = [];

    toString(): string {
        let result = `\u001b[1mEnclaves:\u001b[0m ${this.nodes.join(", ")}\n\u001b[1mDoorways:\u001b[0m\n`;
        for (let a = 0; a < this.edges.length; a++) {
            const e = this.edges[a];
            const before = this.edges.some(
                (x, i) =>
                    x.src.equals(e.dst) &&
                    x.dst.equals(e.src) &&
                    x.label.equals(e.label) &&
                    i < a,
            );
            if (!before) {
                result += `  ${e.src} <-- ${e.label} --> ${e.dst}\n`;
            }
        }
        return result;
    }

    /**
     * Adds a conditional doorway (represented by a State) between two Enclaves
     */
    addEdge(src: Enclave, dst: Enclave, label: State) {
        this.edges.push({ src, dst, label });
        this.edges.push({ src: dst, dst: src, label });
    }

    /**
     * Returns the accessible Enclaves (and any resulting States at those locations) given the initial Enclave and State
     */
    getAccessibleEnclaves(start: EnclaveAndState): EnclaveAndState[] {
        const adjacent: EnclaveAndState[] = [start];
        const visited: EnclaveAndState[] = [start];
        while (adjacent.length > 0) {
            const root: EnclaveAndState = adjacent.pop()!;
            const alternates: EnclaveAndState[] = getAlternates(
                root.enclave.mechanism,
            ).map((x) => ({
                enclave: root.enclave,
                state: new State(...root.state.vars, { ...x, value: x.value }),
            }));
            for (const current of alternates) {
                const neighbors = this.edges.filter(
                    (x) =>
                        x.src.equals(current.enclave) &&
                        current.state.satisfies(x.label),
                );
                for (const n of neighbors) {
                    const transformed: EnclaveAndState = {
                        state: new State(
                            ...current.state.vars,
                            ...n.label.vars,
                        ),
                        enclave: n.dst,
                    };
                    if (
                        !visited.some(
                            (x) =>
                                transformed.enclave.equals(x.enclave) &&
                                transformed.state.equals(x.state),
                        )
                    ) {
                        adjacent.push(transformed);
                        visited.push(transformed);
                    }
                }
            }
        }
        return visited;
    }

    /**
     * Returns a list of all possible States after travelling from the starting Enclave to the destination
     */
    getStatesFromPath = (
        initialState: State,
        src: Enclave,
        dst: Enclave,
    ): State[] =>
        this.getAccessibleEnclaves({
            state: initialState,
            enclave: src,
        })
            .filter((x) => x.enclave.equals(dst))
            .map((x) => x.state);

    getUnusedStateVars = (): StateVar[] =>
        this.nodes
            .map((x) => x.mechanism)
            .filter(
                (x) =>
                    !this.edges.some((y) =>
                        y.label.vars.some((z) => x.id === z.id),
                    ),
            );
}

/**
 * Returns a random element from the given array
 */
const choice = <E>(a: E[]): E => a[Math.floor(Math.random() * a.length)];

/**
 * Returns all alternate values for the given StateVar
 */
function getAlternates(sv: StateVar): StateVar[] {
    if (sv.reversible) {
        const alternates: StateVar[] = [];
        for (let a = 0; a < sv.states; a++) {
            alternates.push({ ...sv, value: a });
        }
        return alternates;
    }
    return sv.value === 0 ? [sv, { ...sv, value: 1 }] : [sv];
}

/**
 * Builds a dungeon from the given initial State
 */
function buildDungeon(initialState: State): Graph {
    const graph = new Graph();
    let currentState: State = initialState;
    graph.nodes.push(new Enclave(initialState.vars[0]));
    let currentEnclave = graph.nodes[0];
    for (let a = 1; a < initialState.vars.length; a++) {
        const anchor: Enclave = choice(graph.nodes);
        const mutables = graph.nodes.filter((x) => x.mutable());
        const numChanges =
            Math.floor(Math.random() * (mutables.length - 1)) + 1;
        const enclave: Enclave = new Enclave(initialState.vars[a]);

        let conditions: StateVar[] = [];
        for (let b = 0; b < numChanges; b++) {
            const diff = choice(mutables);
            mutables.splice(mutables.indexOf(diff), 1);
            const states = graph.getStatesFromPath(
                currentState,
                currentEnclave,
                diff,
            );
            if (states.length > 0) {
                currentState = choice(states);
            } else {
                graph.addEdge(currentEnclave, diff, currentState.relevant());
            }
            const activated = diff.activated(currentState);
            currentEnclave = diff;
            conditions.push(activated);
            currentState = new State(...currentState.vars, activated);
        }
        if (
            graph.getStatesFromPath(currentState, currentEnclave, anchor)
                .length === 0
        ) {
            graph.addEdge(currentEnclave, anchor, currentState.relevant());
        }
        graph.nodes.push(enclave);
        graph.addEdge(anchor, enclave, new State(...conditions));
        currentState = new State(...currentState.vars, ...conditions);
        currentEnclave = enclave;
    }
    return graph;
}

/**
 * Entry point for the algorithm
 */
function main() {
    if (
        process.argv.length != 3 ||
        !process.argv[2].match(/^(b|(r[0-9]+))(:(b|(r[0-9]+)))*$/)
    ) {
        console.log(
            [
                "Usage:\n",
                "  python3 main.py [ri][0-9]+(:[ri][0-9]+)*\n\n",
                "This CLI tool generates state-based puzzle dungeon layouts like those in the Zelda series. ",
                "It inputs a description of the state variables to be navigated in the output dungeon. ",
                "This description must match the regex provided above, where r is for a reversible state variable ",
                "(like a switch that can be turned on and off), ",
                "and i is for an irreversible state variable (like obtaining some special item). ",
                "the number tells this program how many values a state variable can have.\n\n",
                "Happy crawling!",
            ].join(""),
        );
        process.exit(1);
    }

    const dungeon = buildDungeon(
        new State(
            ...process.argv[2].split(":").map((x: string, i: number) => ({
                reversible: x[0] === "r",
                id: String.fromCharCode(65 + i),
                states: x[0] === "b" ? 2 : parseInt(x.substring(1)),
                value: 0,
            })),
        ),
    );
    console.log(dungeon.toString());
    console.log("\u001b[1mUnused enclaves:\u001b[0m");
    let unused = false;
    for (const x of dungeon.getUnusedStateVars()) {
        console.log(new Enclave(x).toString());
        unused = true;
    }
    if (!unused) {
        console.log("\u001b[2mNo enclaves\u001b[0m");
    }
}

main();
