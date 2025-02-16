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

    toEnclaveString(): string {
        return this.vars.reduce((acc, v) => `${acc}${v.id}`, "");
    }

    toFinalString(): string {
        return this.vars.reduce(
            (acc, v) => `${acc}${v.id}(${v.reversible ? "r" : "i"}${v.states})`,
            "",
        );
    }

    changed(): State {
        return new State(
            ...this.vars.map((x: StateVar) => ({
                ...x,
                value: x.reversible
                    ? Math.floor(Math.random() * x.states)
                    : Math.floor(Math.random() * (x.states - 1)) + 1,
            })),
        );
    }

    satisfies(s: State): boolean {
        return s.vars.reduce(
            (acc, x) =>
                acc && this.vars.find((y) => y.id == x.id)?.value == x.value,
            true,
        );
    }
}

type Enclave = State;

type EnclaveAndState = {
    enclave: Enclave;
    state: State;
};

class Graph {
    edges: { src: Enclave; dst: Enclave; label: State | null }[] = [];
    nodes: Enclave[] = [];

    toString(): string {
        let result = `Enclaves: ${this.nodes.map((x) => x.toFinalString()).join(", ")}\nDoorways:\n`;
        for (let a = 0; a < this.edges.length; a++) {
            const e = this.edges[a];
            const before = this.edges.some(
                (x, i) =>
                    equals(x.src, e.dst) &&
                    equals(x.dst, e.src) &&
                    equals(x.label, e.label) &&
                    i < a,
            );
            const after = this.edges.some(
                (x, i) =>
                    equals(x.src, e.dst) &&
                    equals(x.dst, e.src) &&
                    equals(x.label, e.label) &&
                    i > a,
            );
            if (before) {
                continue;
            }
            if (after) {
                result += `  ${e.src.toEnclaveString()} <-${e.label}-> ${e.dst.toEnclaveString()}\n`;
            } else {
                result += `  ${e.src.toEnclaveString()} --${e.label}-> ${e.dst.toEnclaveString()}\n`;
            }
        }
        return result;
    }

    getAccessibleEnclaves(start: EnclaveAndState): EnclaveAndState[] {
        const adjacent: EnclaveAndState[] = [start];
        const visited: EnclaveAndState[] = [start];
        while (adjacent.length > 0) {
            const current: EnclaveAndState = adjacent.pop()!;
            const neighbors = this.edges.filter((x) =>
                x.src == current.enclave && x.label
                    ? current.state.satisfies(x.label)
                    : true,
            );
            for (const n of neighbors) {
                const transformed: EnclaveAndState = {
                    state: new State(
                        ...current.state.vars,
                        ...(n.label?.vars ?? []),
                    ),
                    enclave: n.dst,
                };
                if (!visited.some((x) => equals(transformed, x))) {
                    adjacent.push(transformed);
                    visited.push(transformed);
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
        const valid = accessible.filter((x) => equals(x.enclave, dst));
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

const equals = (x: any, y: any) =>
    x &&
    y &&
    typeof x === "object" &&
    typeof y === "object" &&
    Object.keys(x).length === Object.keys(y).length
        ? Object.keys(x).reduce((acc, k) => acc && equals(x[k], y[k]), true)
        : x === y;

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
graph.nodes.push(new State(initialState.vars[0]));
for (let a = 1; a < initialState.vars.length; a++) {
    const enclave: Enclave = new State(initialState.vars[a]);
    const anchor: Enclave = choice(graph.nodes);
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
    if (loop?.satisfies(condition)) {
        currentState = loop;
    } else if (graph.getStateFromPath(currentState, condition, anchor)) {
        const diff = anchor.changed();
        graph.edges.push({
            src: anchor,
            dst: condition,
            label: diff,
        });
        graph.edges.push({
            src: condition,
            dst: anchor,
            label: diff,
        });
        currentState = new State(
            ...graph.getStateFromPath(
                new State(...currentState.vars, ...diff.vars),
                condition,
                anchor,
            )!.vars,
            ...condition.vars,
        );
    } else {
        // Add another mechanism to the anchor enclave?
        throw new Error("Uh oh :(");
    }
    graph.edges.push({
        src: anchor,
        dst: enclave,
        label: condition,
    });
    graph.edges.push({
        src: enclave,
        dst: anchor,
        label: condition,
    });
}
console.log(graph.toString());
