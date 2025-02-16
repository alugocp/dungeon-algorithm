type StateVar = {
    id: string;
    states: number;
    value: number;
    reversible: boolean;
};

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

    toString(): string {
        return this.vars.reduce((acc, v) => `${acc}${v.id}${v.value}`, "");
    }

    relevant(): State {
        return new State(
            ...this.vars.filter((x) => x.reversible || x.value > 0),
        );
    }

    satisfies(s: State): boolean {
        return s.vars.reduce(
            (acc, x) =>
                acc && this.vars.find((y) => y.id === x.id)?.value === x.value,
            true,
        );
    }

    equals(s: State): boolean {
        return (
            this.vars.length === s.vars.length &&
            this.vars.reduce(
                (acc: boolean, x: StateVar, i: number) =>
                    acc && x.id === s.vars[i].id && x.value === s.vars[i].value,
                true,
            )
        );
    }
}

class Enclave {
    constructor(public readonly mechanism: StateVar) {}

    toString(): string {
        return `${this.mechanism.id}(${this.mechanism.reversible ? "r" : "i"}${this.mechanism.states})`;
    }

    changed(): State {
        return new State({
            ...this.mechanism,
            value: this.mechanism.reversible
                ? Math.floor(Math.random() * this.mechanism.states)
                : Math.floor(Math.random() * (this.mechanism.states - 1)) + 1,
        });
    }

    equals(s: Enclave): boolean {
        return (
            this.mechanism.id === s.mechanism.id &&
            this.mechanism.value === s.mechanism.value
        );
    }
}

type EnclaveAndState = {
    enclave: Enclave;
    state: State;
};

class Graph {
    edges: { src: Enclave; dst: Enclave; label: State }[] = [];
    nodes: Enclave[] = [];

    toString(): string {
        let result = `Enclaves: ${this.nodes.join(", ")}\nDoorways:\n`;
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
                result += `  ${e.src} <-${e.label}-> ${e.dst}\n`;
            }
        }
        return result;
    }

    addEdge(src: Enclave, dst: Enclave, label: State) {
        this.edges.push({ src, dst, label });
        this.edges.push({ src: dst, dst: src, label });
    }

    getAccessibleEnclaves(start: EnclaveAndState): EnclaveAndState[] {
        const adjacent: EnclaveAndState[] = [start];
        const visited: EnclaveAndState[] = [start];
        while (adjacent.length > 0) {
            const root: EnclaveAndState = adjacent.pop()!;
            const alternates: EnclaveAndState[] = [];
            if (root.enclave.mechanism.reversible) {
                for (let a = 0; a < root.enclave.mechanism.states; a++) {
                    alternates.push({
                        enclave: root.enclave,
                        state: new State(...root.state.vars, {
                            ...root.enclave.mechanism,
                            value: a,
                        }),
                    });
                }
            } else {
                alternates.push({
                    enclave: root.enclave,
                    state: new State(...root.state.vars, {
                        ...root.enclave.mechanism,
                        value: 1,
                    }),
                });
            }
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

    getStateFromPath(
        initialState: State,
        src: Enclave,
        dst: Enclave,
    ): State | null {
        const accessible = this.getAccessibleEnclaves({
            state: initialState,
            enclave: src,
        });
        const valid = accessible.filter((x) => x.enclave.equals(dst));
        return valid.length > 0 ? choice(valid).state : null;
    }

    getStateFromLoop(
        initialState: State,
        src: Enclave,
        dst: Enclave,
        diff: State | null,
    ): State | null {
        const state = this.getStateFromPath(initialState, src, dst);
        return state
            ? this.getStateFromPath(
                  new State(...state.vars, ...(diff ? diff.vars : [])),
                  dst,
                  src,
              )
            : null;
    }
}

const choice = <E>(a: E[]): E => a[Math.floor(Math.random() * a.length)];

if (
    process.argv.length != 3 ||
    !process.argv[2].match(/[ri][0-9]+(:[ri][0-9]+)*/)
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

const initialState: State = new State(
    ...process.argv[2].split(":").map((x: string, i: number) => ({
        reversible: x[0] === "r",
        id: String.fromCharCode(65 + i),
        states: parseInt(x.substring(1)),
        value: 0,
    })),
);

const graph = new Graph();
let currentState: State = initialState;
graph.nodes.push(new Enclave(initialState.vars[0]));
let currentEnclave = graph.nodes[0];
for (let a = 1; a < initialState.vars.length; a++) {
    const anchor: Enclave = choice(graph.nodes);
    if (currentEnclave !== anchor) {
        const path = graph.getStateFromPath(
            currentState,
            currentEnclave,
            anchor,
        );
        if (path) {
            currentState = path;
        } else {
            graph.addEdge(currentEnclave, anchor, currentState.relevant());
        }
    }

    const enclave: Enclave = new Enclave(initialState.vars[a]);
    const doorway: EnclaveAndState = choice(
        graph.getAccessibleEnclaves({
            state: currentState,
            enclave: anchor,
        }),
    );
    const condition = doorway.enclave.changed();
    const loop = graph.getStateFromLoop(
        currentState,
        anchor,
        doorway.enclave,
        condition,
    );
    graph.nodes.push(enclave);
    graph.addEdge(anchor, enclave, condition);
    if (loop?.satisfies(condition)) {
        currentState = loop;
    } else if (anchor.mechanism.id !== condition.vars[0].id) {
        const diff = anchor.changed();
        graph.addEdge(anchor, new Enclave(condition.vars[0]), diff);
        currentState = new State(...currentState.vars, ...diff.vars);
    }
    currentEnclave = enclave;
}
console.log(graph.toString());
