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

    toString = (): string =>
        this.vars.reduce((acc, v) => `${acc}${v.id}${v.value}`, "");

    relevant = (): State =>
        new State(...this.vars.filter((x) => x.reversible || x.value > 0));

    satisfies = (s: State): boolean =>
        s.vars.reduce(
            (acc, x) =>
                acc && this.vars.find((y) => y.id === x.id)?.value === x.value,
            true,
        );

    equals = (s: State): boolean =>
        this.vars.length === s.vars.length &&
        this.vars.reduce(
            (acc: boolean, x: StateVar, i: number) =>
                acc && x.id === s.vars[i].id && x.value === s.vars[i].value,
            true,
        );
}

class Enclave {
    constructor(public readonly mechanism: StateVar) {}

    toString = (): string =>
        `${this.mechanism.id}(${this.mechanism.reversible ? `r${this.mechanism.states}` : "b"})`;

    mutable = (): boolean =>
        this.mechanism.reversible || this.mechanism.value === 0;

    equals = (s: Enclave): boolean => this.mechanism.id === s.mechanism.id;

    activated = (): StateVar => ({
        ...this.mechanism,
        value: this.mechanism.reversible
            ? Math.floor(Math.random() * this.mechanism.states)
            : Math.floor(Math.random() * (this.mechanism.states - 1)) + 1,
    });
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
}

const choice = <E>(a: E[]): E => a[Math.floor(Math.random() * a.length)];

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
            const activated = diff.activated();
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
    }
    return graph;
}

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
