"""
Generates puzzlebox dungeons like those seen in the Zelda series
"""

from typing import Generic, TypeVar, Self, Tuple
from itertools import chain, combinations
from dataclasses import dataclass
from copy import copy, deepcopy
from functools import reduce
from sys import argv, exit
from random import choice
from re import fullmatch
from math import inf


class Ansi:
    """
    ANSI codes for different text styles
    """

    bold = lambda x: f"\x1b[1m{x}\x1b[0m"
    faint = lambda x: f"\x1b[2m{x}\x1b[0m"
    underline = lambda x: f"\x1b[4m{x}\x1b[0m"
    green = lambda x: f"\x1b[32m{x}\x1b[0m"


@dataclass
class StateVar:
    """
    Represents a single component of State
    """

    id: str
    reversible: bool
    states: int
    value: int = 0


class State:
    """
    Represents some global state that a dungeon can be in
    """

    state_vars: list[StateVar]

    def __init__(self, state_vars: list[StateVar] = []):
        self.state_vars = state_vars

    def __str__(self) -> str:
        return ":".join([(x.id + str(x.value)) for x in self.state_vars])

    def add(self, other: StateVar):
        """ """
        pass

    def apply(self, other: Self):
        """ """
        for state_var in other.state_vars:
            next(filter(lambda x: x.id == state_var.id, self.state_vars)).value = (
                state_var.value
            )

    def accessible(self, other: Self) -> bool:
        """ """
        for state_var in other.state_vars:
            if (
                next(filter(lambda x: x.id == state_var.id, self.state_vars)).value
                != state_var.value
            ):
                return False
        return True

    def random_subset(self) -> Self:
        """ """
        return State([choice(self.state_vars)])


class Enclave:
    """
    Represents a collection of mutually accessible rooms in the dungeon
    """

    mechanisms: State

    def __init__(self, initial: StateVar | None = None):
        self.mechanisms = State() if initial is None else State([initial])

    def __str__(self) -> str:
        return (
            "Boss"
            if len(self.mechanisms.state_vars) == 0
            else "".join(map(lambda x: x.id, self.mechanisms.state_vars))
        )


class Dungeon:
    """ """

    enclaves: list[Enclave]
    doorways: dict[Enclave, list[Tuple[Enclave, State]]]

    def __init__(self):
        self.enclaves = []
        self.doorways = {}

    def add_node(self, enclave: Enclave):
        """ """
        self.enclaves.append(enclave)
        self.doorways[enclave] = []

    def add_edge(self, n1: Enclave, n2: Enclave, doorway: State):
        """ """
        self.doorways[n1].append((n2, doorway))
        self.doorways[n2].append((n1, doorway))

    def get_neighbors(self, enclave: Enclave) -> list[Tuple[Enclave, State]]:
        """ """
        return self.doorways[enclave]

    def __str__(self) -> str:
        result = (
            Ansi.bold("Nodes: ")
            + ", ".join(list(map(str, self.enclaves)))
            + "\n"
            + Ansi.bold("Edges:")
        )
        edges = []
        for n1 in self.doorways:
            for n2, e in self.doorways[n1]:
                left = Ansi.green(n1)
                mid = Ansi.faint(e)
                right = Ansi.faint(n2)
                edges.append(f"\n  {left} -- {mid} --> {right}")
        result += "".join(edges) if len(edges) > 0 else " none"
        return result


def get_accessible_mechanisms(
    d: Dungeon, enclave: Enclave, current_state: State
) -> State:
    """ """
    accessible = State(enclave.mechanisms.state_vars)
    adjacent = [enclave]
    visited = []
    while len(adjacent) > 0:
        n1 = adjacent.pop(0)
        visited.append(n1)
        for n2, e in d.get_neighbors(n1):
            if n2 not in visited and (
                current_state.satisfies(e) or accessible.satisfies(e)
            ):
                adjacent.append(n2)
                accessible.add(e)
    return accessible


def add_enclave(d: Dungeon, mechanisms: list[StateVar], current_state: State):
    """ """
    state_change = choice(mechanisms)
    mechanisms.remove(state_change)
    enclave = Enclave(state_change)
    if len(d.enclaves) == 0:
        d.add_node(enclave)
        return
    anchor = choice(d.enclaves)
    delta = get_accessible_mechanisms(d, anchor, current_state).random_subset()
    d.add_node(enclave)
    d.add_edge(enclave, anchor, delta)
    current_state.apply(delta)


def main(initial_state: State):
    """
    Generates and displays a new dungeon
    """
    mechanisms = copy(initial_state.state_vars)
    current_state = initial_state
    d = Dungeon()
    while len(mechanisms) > 0:
        add_enclave(d, mechanisms, current_state)
    boss = Enclave()
    anchor = choice(d.enclaves)
    delta = get_accessible_mechanisms(d, anchor, current_state).random_subset()
    d.add_node(boss)
    d.add_edge(boss, anchor, delta)
    print(d)


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
        map(
            lambda x: StateVar(chr(ord("A") + x[0]), x[1][0] == "r", int(x[1][1:])),
            enumerate(argv[1].split(":")),
        )
    )
    main(State(input_vars))
