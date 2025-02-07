from typing import Generic, TypeVar, Self
from functools import reduce
from random import choice
from copy import deepcopy
from dataclasses import dataclass
from math import inf


N = TypeVar("N")
E = TypeVar("E")


class Graph(Generic[N, E]):
    nodes: list[N]
    edges: dict[str, E]

    def __init__(self):
        self.nodes = []
        self.edges = {}

    def add_node(self, node: N):
        self.nodes.append(node)

    def add_edge(self, n1: N, n2: N, label: E, directional=False):
        self.edges[self.get_edge_hash(n1, n2)] = label
        if not directional:
            self.edges[self.get_edge_hash(n2, n1)] = label

    def get_edge_hash(self, n1: N, n2: N) -> str:
        return str(hash(n1)) + ":" + str(hash(n2))

    def get_neighbors(self, node: N) -> list[N]:
        h = hash(node)
        neighbors: list[N] = []
        for n in self.nodes:
            if node != n and self.get_edge_hash(node, n) in self.edges.keys():
                neighbors.append(n)
        return neighbors

    def random_walk(self) -> list[N]:
        walk: list[N] = []
        options = [self.nodes[0]]
        while len(options) > 0:
            walk.append(choice(options))
            options = list(
                filter(lambda x: x not in walk, self.get_neighbors(walk[-1]))
            )
        return walk

    def __str__(self) -> str:
        result = (
            "Nodes: " + ", ".join(list(map(lambda x: str(x), self.nodes))) + "\nEdges:"
        )
        edges = False
        for i1 in range(len(self.nodes) - 1):
            for i2 in range(i1 + 1, len(self.nodes)):
                n1 = self.nodes[i1]
                n2 = self.nodes[i2]
                right = self.get_edge_hash(n1, n2) in self.edges.keys()
                left = self.get_edge_hash(n2, n1) in self.edges.keys()
                if right or left:
                    r = ">" if right else "-"
                    l = "<" if left else "-"
                    result += f"\n  {n1} {l}-{r} {n2}"
                    edges = True
        if not edges:
            result += " N/A"
        return result


@dataclass
class StateVar:
    reversible: bool
    states: int
    value: int = 0


class State:
    vars: list[StateVar]

    def __init__(self, vars: list[StateVar]):
        self.vars = vars

    def __str__(self) -> str:
        return "".join(
            [["F", "T"][x.value] if x.states == 2 else x.value for x in self.vars]
        )

    def all_are_max(self):
        for var in self.vars:
            if var.value < var.states - 1:
                return False
        return True

    def increment(self):
        i = len(self.vars) - 1
        while i >= 0:
            if self.vars[i].value == self.vars[i].states - 1:
                self.vars[i].value = 0
                i -= 1
            else:
                self.vars[i].value += 1
                break

    def __hash__(self) -> int:
        value = 1 if self.vars[0].value == inf else self.vars[0].value
        coeff = self.vars[0].states
        for i in range(1, len(self.vars)):
            value += coeff * (1 if self.vars[i].value == inf else self.vars[i].value)
            coeff *= self.vars[i].states
        return value

    def __eq__(self, other: Self) -> bool:
        for i in range(len(self.vars)):
            if self.vars[i] != other.vars[i]:
                return False
        return True

    def __sub__(self, other: Self) -> Self:
        vars = deepcopy(self.vars)
        for i in range(len(self.vars)):
            vars[i].value = self.vars[i].value - other.vars[i].value
        return StateDiff(vars)


class StateDiff(State):

    def __init__(self, vars: list[StateVar]):
        super().__init__(vars)
        for var in self.vars:
            if var.value != 0 and var.reversible:
                var.value = inf

    def __str__(self) -> str:
        mask = {inf: "*", 0: "."}
        return "".join(
            [mask[x.value] if x.value in mask else str(x.value) for x in self.vars]
        )

    def relevant(self) -> StateVar:
        return next(filter(lambda x: x.value != 0, self.vars))

    def __abs__(self) -> int:
        return reduce(
            lambda acc, x: acc + abs(1 if x.value == inf else x.value), self.vars, 0
        )


class Enclave:
    mechanism: StateDiff | None
    turned_on: list[State] = []

    def __init__(self, mechanism: StateDiff | None):
        self.mechanism = mechanism

    def __str__(self) -> str:
        return "Boss" if self.mechanism is None else str(self.mechanism)

    def __eq__(self, other: Self) -> bool:
        return self.mechanism == other.mechanism

    def __hash__(self) -> int:
        return 0 if self.mechanism is None else hash(self.mechanism)

    def is_boss_enclave(self) -> bool:
        return self.mechanism is None

    def add_state(self, s: State):
        self.turned_on.append(s)


StateGraph = Graph[State, None]
Dungeon = Graph[Enclave, None]


def generate_state_graph(initial_state: State) -> StateGraph:
    g: StateGraph = Graph()
    curr = initial_state
    g.add_node(curr)
    while not curr.all_are_max():
        curr = deepcopy(curr)
        curr.increment()
        for n in g.nodes:
            diff = n - curr
            if abs(diff) == 1:
                g.add_edge(n, curr, None, not diff.relevant().reversible)
        g.add_node(curr)
    return g


def get_enclaves(state_walk) -> Dungeon:
    g: Dungeon = Graph()
    for i in range(1, len(state_walk)):
        diff = state_walk[i] - state_walk[i - 1]
        if Enclave(diff) not in g.nodes:
            g.add_node(Enclave(diff))
    g.add_node(Enclave(None))
    return g


def main(initial_state: State):
    state_graph = generate_state_graph(initial_state)
    print("STATE GRAPH")
    print(state_graph)
    print("")

    state_walk = state_graph.random_walk()
    print("STATE WALK")
    print(", ".join(map(lambda x: str(x), state_walk)))
    print("")

    enclaves = get_enclaves(state_walk)
    print("ENCLAVES")
    print(enclaves)


if __name__ == "__main__":
    main(State([StateVar(False, 2), StateVar(False, 2), StateVar(True, 2)]))
