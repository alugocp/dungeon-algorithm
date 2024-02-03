'''
This module implements the dungeon generation algorithm
'''
import sys
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

# Set up state graph:
# • Read input config to get types of state change and final state(s)
# • Calculate all possible states and create nodes for them
# • Use the types of state change to add edges to the state nodes
# • Make sure all state paths converge upon a final state
# • Prune disconnected state nodes

# Generate dungeon layout:
# • Create W x H rooms (nodes) and generate an enclave for each unique state change + 1
#   (final room's enclave)
# • Assign each enclave (minus the last one) to some state change
# • At each state node, connect the enclave represented by its edges to the enclave(s)
#   represented by the connected state node's edges with a conditional passage
# • Throw in some one-way doors to "earlier" enclaves (based on state graph path traversal order)


# TYPES AND CONSTANTS SECTION


class StateChangeType(Enum):
    '''
    Defines the canonical state change types that this algorithm can process
    '''
    BINARY_REVERSIBLE = 'binary reversible'
    BINARY_IRREVERSIBLE = 'binary irreversible'
    BINARY_CYCLIC = 'binary cyclic'
    NUMERIC_OPTIONAL = 'numeric optional'
    NUMERIC_IRREVERSIBLE = 'numeric irreversible'
    NUMERIC_CYCLIC = 'numeric cyclic'


@dataclass
class DungeonConfig:
    '''
    Represents some input config when generating a dungeon
    '''
    # List of state change types. The int must be 2 for
    # binary types and cannot be greater than len(STATES)
    states: List[Tuple[StateChangeType, int]]
    w: int # Width of the rooms rectangle
    h: int # Height of the rooms rectangle


# Represents the values for a single state
STATES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']


class Graph:
    '''
    Abstraction for a graph
    '''
    _nodes: List[str] = []
    _edges: Dict[str, List[str]] = {}

    def add_node(self, node: str) -> ():
        self._nodes.append(node)

    def remove_node(self, node: str) -> ():
        self._nodes.remove(node)

    def add_edge(self, n1: str, n2: str, bidirectional = False) -> ():
        if n1 not in self._edges:
            self._edges[n1] = []
        self._edges[n1].append(n2)
        if bidirectional:
            if n2 not in self._edges:
                self._edges[n2] = []
            self._edges[n2].append(n1)

    def remove_edge(self, n1: str, n2: str, bidirectional = False) -> ():
        self._edges[n1].remove(n2)
        if bidirectional:
            self._edges[n2].remove(n1)

    def print(self) -> ():
        sys.stdout.write('Nodes: ')
        sys.stdout.write(', '.join(self._nodes))
        sys.stdout.write('\nEdges:\n')
        for n1, n2s in self._edges:
            for n2 in n2s:
                print(f'• {n1} -> {n2}')


# GENERATE STATE GRAPH SECTION


def generate_all_states(config: DungeonConfig) -> List[str]:
    '''
    Generates all combinations of dungeon state by its config
    '''
    pieces = []
    for a in range(len(config.states)):
        pieces.append([(str(a) + STATES[x]) for x in range(config.states[a][1])])
    return get_all_combinations(pieces)


def get_all_combinations(list_of_lists: List[List[str]]) -> List[str]:
    '''
    Returns all combinations of the elements in a list of lists.
    Helper method for generate_all_states()
    '''
    indices = [ 0 for x in range(len(list_of_lists)) ]
    results = []
    done = False
    while not done:
        results.append(''.join(
            list(map(lambda xy: list_of_lists[xy[0]][xy[1]], enumerate(indices)))
        ))
        a = 0
        while True:
            indices[a] += 1
            if indices[a] == len(list_of_lists[a]):
                indices[a] = 0
                a += 1
                if a == len(indices):
                    done = True
                    break
                continue
            break
    return results


# MAIN SECTION


def generate_dungeon():
    '''
    Runs the entire algorithm to generate a dungeon
    '''
    config = DungeonConfig([('numeric cyclic', 3), ('binary reversible', 2)], 5, 4)
    all_states = generate_all_states(config)
    state_graph = Graph()
    for state in all_states:
        state_graph.add_node(state)
    state_graph.print()


if __name__ == '__main__':
    generate_dungeon()
