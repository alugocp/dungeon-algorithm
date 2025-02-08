"""
Generates puzzlebox dungeons like those seen in the Zelda series
"""

from typing import Generic, TypeVar, Self
from itertools import chain, combinations
from dataclasses import dataclass
from functools import reduce
from sys import argv, exit
from random import choice
from copy import deepcopy
from re import fullmatch
from math import inf


class Styled:
    """
    Wrapper for ANSI terminal escaped strings
    """

    BOLD = "1"
    FAINT = "2"
    UNDERLINE = "4"
    GREEN = "32"
    codes: list[str]

    def __init__(self, obj, codes):
        self.obj = obj
        self.codes = codes

    def __str__(self) -> str:
        return "\x1b[" + ";".join(self.codes) + "m" + str(self.obj) + "\x1b[0m"


# Generic type definitions for the Graph class
N = TypeVar("N")
E = TypeVar("E")


class Graph(Generic[N, E]):
    """
    Generic implementation of a collection of nodes and edges
    """

    nodes: list[N]
    edges: dict[str, E]

    def __init__(self):
        self.nodes = []
        self.edges = {}

    def add_node(self, node: N):
        """
        Adds a node to the Graph
        """
        self.nodes.append(node)

    def add_edge(self, n1: N, n2: N, label: E, directional=False):
        """
        Adds an edge to the Graph
        """
        self.edges[self.get_edge_hash(n1, n2)] = label
        if not directional:
            self.edges[self.get_edge_hash(n2, n1)] = label

    def get_node(self, n: N) -> N:
        """
        Returns the first node in this Graph that matches the given node
        """
        return next(filter(lambda x: x == n, self.nodes))

    def get_edge(self, n1: N, n2: N) -> E | None:
        """
        Returns the label on the edge between the given nodes
        """
        key = self.get_edge_hash(n1, n2)
        return self.edges[key] if key in self.edges else None

    def get_edge_hash(self, n1: N, n2: N) -> str:
        """
        Returns a unique value for the edge between the given nodes
        """
        return str(hash(n1)) + ":" + str(hash(n2))

    def get_neighbors(self, node: N) -> list[N]:
        """
        Returns all nodes that the given node points to
        """
        neighbors: list[N] = []
        for n in self.nodes:
            if node != n and self.get_edge_hash(node, n) in self.edges:
                neighbors.append(n)
        return neighbors

    def random_walk(self) -> list[N]:
        """
        Returns a random path through the Graph
        """
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
            str(Styled("Nodes: ", [Styled.BOLD]))
            + ", ".join(list(map(str, self.nodes)))
            + "\n"
            + str(Styled("Edges:", [Styled.BOLD]))
        )
        edges = False
        for i1 in range(len(self.nodes) - 1):
            for i2 in range(i1 + 1, len(self.nodes)):
                n1 = self.nodes[i1]
                n2 = self.nodes[i2]
                right = self.get_edge_hash(n1, n2) in self.edges
                left = self.get_edge_hash(n2, n1) in self.edges
                if right or left:
                    r = ">" if right else "-"
                    l = "<" if left else "-"
                    result += (
                        "\n  "
                        + str(Styled(n1, [Styled.GREEN]))
                        + f" {l}-{r} "
                        + str(Styled(n2, [Styled.GREEN]))
                    )
                    el2r = self.get_edge(n1, n2)
                    er2l = self.get_edge(n2, n1)
                    if el2r == er2l:
                        if el2r is not None:
                            result += " (" + str(Styled(el2r, [Styled.GREEN])) + ")"
                    else:
                        if el2r is not None:
                            result += " (" + str(Styled(el2r, [Styled.GREEN])) + ")>"
                        if er2l is not None:
                            result += " <(" + str(Styled(er2l, [Styled.GREEN])) + ")"
                    edges = True
        if not edges:
            result += " N/A"
        return result


class PrettyPrintSet(set):
    """
    A set that actually stringifies its elements
    """

    def __init__(self, parent):
        for x in parent:
            self.add(x)

    def __str__(self) -> str:
        return "{" + ", ".join([str(x) for x in self]) + "}"


@dataclass
class StateVar:
    """
    Represents a single component of State
    """

    reversible: bool
    states: int
    value: int = 0


class State:
    """
    Represents some global state that a dungeon can be in
    """

    state_vars: list[StateVar]

    def __init__(self, state_vars: list[StateVar]):
        self.state_vars = state_vars

    def __str__(self) -> str:
        return "".join(
            [
                ["F", "T"][x.value] if x.states == 2 else str(x.value)
                for x in self.state_vars
            ]
        )

    def all_are_max(self) -> bool:
        """
        Returns True if all StateVars have their maximum value
        """
        for var in self.state_vars:
            if var.value < var.states - 1:
                return False
        return True

    def increment(self):
        """
        Increments this State by 1
        """
        i = len(self.state_vars) - 1
        while i >= 0:
            if self.state_vars[i].value == self.state_vars[i].states - 1:
                self.state_vars[i].value = 0
                i -= 1
            else:
                self.state_vars[i].value += 1
                break

    def __hash__(self) -> int:
        value = 1 if self.state_vars[0].value == inf else self.state_vars[0].value
        coeff = self.state_vars[0].states
        for i in range(1, len(self.state_vars)):
            value += coeff * (
                1 if self.state_vars[i].value == inf else self.state_vars[i].value
            )
            coeff *= self.state_vars[i].states
        return value

    def __eq__(self, other: Self) -> bool:
        for i in range(len(self.state_vars)):
            if self.state_vars[i] != other.state_vars[i]:
                return False
        return True

    def __sub__(self, other: Self) -> Self:
        state_vars = deepcopy(self.state_vars)
        for i in range(len(self.state_vars)):
            state_vars[i].value = self.state_vars[i].value - other.state_vars[i].value
        return StateDiff(state_vars)

    @staticmethod
    def common(states: list[Self]) -> Self:
        """
        Returns a PartialState with only the StateVars that these States have in common
        """
        result = deepcopy(states[0].state_vars)
        for state in states[1:]:
            for i in range(len(state.state_vars)):
                if state.state_vars[i].value != result[i].value:
                    result[i].value = None
        return PartialState(result)


class PartialState(State):
    """
    Represents a subset of a global State
    """

    def __str__(self) -> str:
        return "".join(
            [
                (
                    "."
                    if x.value is None
                    else (["F", "T"][x.value] if x.states == 2 else str(x.value))
                )
                for x in self.state_vars
            ]
        )

    def matches(self, other: State) -> bool:
        """
        Returns True if this PartialState contains similar values to the given State
        """
        return reduce(
            lambda acc, i: acc
            and (self.state_vars[i].value in [None, other.state_vars[i].value]),
            list(range(len(self.state_vars))),
            True,
        )

    def matches_none(self, states: set[State]) -> bool:
        """
        Returns True if this PartialState does not match any of the given States
        """
        for s in states:
            if self.matches(s):
                return False
        return True

    def get_subsets(self) -> list[State]:
        """
        Grabs all possible subsets of this PartialState objects, ordered from least cardinality to highest
        """
        result: list[State] = []
        relevant_indices = list(
            filter(
                lambda x: x is not None,
                [
                    None if self.state_vars[i].value is None else i
                    for i in range(len(self.state_vars))
                ],
            )
        )
        powerset = chain.from_iterable(
            combinations(relevant_indices, x) for x in range(len(relevant_indices) + 1)
        )
        next(powerset)
        basis = deepcopy(self.state_vars)
        for var in basis:
            var.value = None
        for p in powerset:
            rehydrated = deepcopy(basis)
            for i in list(p):
                rehydrated[i].value = self.state_vars[i].value
            result.append(PartialState(rehydrated))
        return result


class StateDiff(State):
    """
    Represents the difference between two State objects
    """

    def __init__(self, state_vars: list[StateVar]):
        super().__init__(state_vars)
        for var in self.state_vars:
            if var.value != 0 and var.reversible:
                var.value = inf

    def __str__(self) -> str:
        mask = {inf: "*", 0: "."}
        return "".join(
            [
                mask[x.value] if x.value in mask else str(x.value)
                for x in self.state_vars
            ]
        )

    def relevant(self) -> StateVar:
        """
        Returns the first StateVar with a non-zero value
        """
        return next(filter(lambda x: x.value != 0, self.state_vars))

    def __abs__(self) -> int:
        return reduce(
            lambda acc, x: acc + abs(1 if x.value == inf else x.value),
            self.state_vars,
            0,
        )


class Enclave:
    """
    Represents a collection of mutually accessible rooms in the dungeon
    """

    mechanism: StateDiff | None
    turned_on: set[State]

    def __init__(self, mechanism: StateDiff | None):
        self.mechanism = mechanism
        self.turned_on = set()

    def __str__(self) -> str:
        return (
            ("Boss" if self.mechanism is None else str(self.mechanism))
            + " "
            + str(Styled(PrettyPrintSet(self.turned_on), [Styled.FAINT]))
        )

    def __eq__(self, other: Self) -> bool:
        return other is not None and self.mechanism == other.mechanism

    def __hash__(self) -> int:
        return 0 if self.mechanism is None else hash(self.mechanism)

    def is_boss_enclave(self) -> bool:
        """
        Returns True if this is the last Enclave in the dungeon
        """
        return self.mechanism is None

    def add_state(self, s: State):
        """
        Adds a State in which this Enclave will be accessible
        """
        self.turned_on.add(s)


# Convenient type definitions
StateGraph = Graph[State, None]
Dungeon = Graph[Enclave, PrettyPrintSet[State]]


def generate_state_graph(initial_state: State) -> StateGraph:
    """
    Generates a Graph of all possible States given some initial State
    """
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
    """
    Returns a Graph of dungeon Enclaves without any edges yet
    """
    g: Dungeon = Graph()
    inert: set[Enclave] = set()
    for i in range(1, len(state_walk)):
        diff = state_walk[i] - state_walk[i - 1]
        enclave = Enclave(diff)
        newly_inert = None
        if enclave in g.nodes:
            enclave = g.get_node(enclave)
        else:
            g.add_node(enclave)
            if not diff.relevant().reversible:
                newly_inert = enclave
                inert.add(enclave)
        enclave.add_state(state_walk[i - 1])
        enclave.add_state(state_walk[i])
        for e in filter(lambda x: x != newly_inert, inert):
            e.add_state(state_walk[i])
    boss = Enclave(None)
    g.add_node(boss)
    boss.add_state(state_walk[-1])
    return g


def add_conditional_doors(d: Dungeon):
    """
    Adds conditional doors as edges in a Graph of Enclaves
    """
    for i1 in range(len(d.nodes) - 1):
        for i2 in range(i1, len(d.nodes)):
            intersection = PrettyPrintSet(d.nodes[i1].turned_on & d.nodes[i2].turned_on)
            d.add_edge(d.nodes[i1], d.nodes[i2], intersection)


def simplify_conditional_doors(d: Dungeon):
    """
    Simplifies the State needed to pass between Enclaves
    """
    for i1 in range(len(d.nodes) - 1):
        for i2 in range(i1 + 1, len(d.nodes)):
            intersection = d.get_edge(d.nodes[i1], d.nodes[i2])
            if len(intersection) == 0:
                continue
            diff = (d.nodes[i1].turned_on | d.nodes[i2].turned_on) - intersection
            common = State.common(list(intersection))
            for subset in common.get_subsets():
                if subset.matches_none(diff):
                    print(
                        str(Styled(d.nodes[i1], [Styled.GREEN]))
                        + " <-> "
                        + str(Styled(d.nodes[i2], [Styled.GREEN]))
                        + " ("
                        + str(Styled(intersection, [Styled.GREEN]))
                        + f") ---> {subset}"
                    )
                    break


def main(initial_state: State):
    """
    Generates and displays a new dungeon
    """
    state_graph = generate_state_graph(initial_state)
    print(Styled("State Graph", [Styled.UNDERLINE]))
    print(state_graph)
    print("")

    state_walk = state_graph.random_walk()
    print(Styled("State Walk", [Styled.UNDERLINE]))
    print(" -> ".join(map(str, state_walk)))
    print("")

    dungeon = get_enclaves(state_walk)
    add_conditional_doors(dungeon)
    print(Styled("Dungeon Enclaves", [Styled.UNDERLINE]))
    print(dungeon)
    print("")

    print(Styled("Simplified Passages", [Styled.UNDERLINE]))
    simplify_conditional_doors(dungeon)


def print_help():
    """
    Displays usage options and an explanation of this CLI tool
    """
    desc = "".join(
        [
            "Usage:\n"
            "  python3 main.py [ri][0-9]+(:[ri][0-9]+)*\n\n"
            "This CLI tool generates state-based puzzle dungeon layouts like those in the Zelda series. "
            "It inputs a description of the state variables to be navigated in the output dungeon. "
            "This description must match the regex provided above, where r is for a reversible state variable "
            "(like a switch that can be turned on and off), "
            "and i is for an irreversible state variable (like obtaining some special item). "
            "the number tells this program how many values a state variable can have.\n\n"
            "Happy crawling!"
        ]
    )
    print(desc)


if __name__ == "__main__":
    if len(argv) != 2 or not fullmatch("[ri][0-9]+(:[ri][0-9]+)*", argv[1]):
        print_help()
        exit(1)

    input_vars = list(
        map(lambda x: StateVar(x[0] == "r", int(x[1:])), argv[1].split(":"))
    )
    main(State(input_vars))
