from typing import Generic, TypeVar, Self
from functools import reduce
from random import choice
from copy import deepcopy


class StateVar:
    reversible: bool
    states: int
    value: int

    def __init__(self, reversible: bool, states: int):
        self.reversible = reversible
        self.states = states
        self.value = 0

    def __str__(self) -> str:
        if self.states == 2:
            return ["F", "T"][self.value]
        return str(self.value)


class State:
    vars: list[StateVar]

    def __init__(self, vars: list[StateVar]):
        self.vars = vars

    def __str__(self) -> str:
        return "".join(list(map(lambda x: str(x), self.vars)))

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

    def __sub__(self, other: Self) -> Self:
        result = deepcopy(self)
        for i in range(len(self.vars)):
            result.vars[i].value = self.vars[i].value - other.vars[i].value
        return result

    def __abs__(self) -> int:
        return reduce(lambda acc, x: acc + abs(x.value), self.vars, 0)

    def relevant(self) -> StateVar:
        return next(filter(lambda x: x.value != 0, self.vars))


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


def generate_state_graph(initial_state: State) -> Graph[State, None]:
    g: Graph[State, None] = Graph()
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


def get_enclaves(state_walk):
    pass


def main(initial_state: State):
    state_graph = generate_state_graph(initial_state)
    print("STATE GRAPH")
    print(state_graph)
    print("")

    state_walk = state_graph.random_walk()
    print("STATE WALK")
    print(", ".join(map(lambda x: str(x), state_walk)))
    # enclaves = get_enclaves(state_walk)


if __name__ == "__main__":
    main(State([StateVar(False, 2), StateVar(False, 2), StateVar(True, 2)]))
