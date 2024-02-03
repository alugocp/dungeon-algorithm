'''
This module implements the dungeon generation algorithm
'''
import re
import sys
import random
from typing import List, Tuple, Dict, Set, Optional
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
    # binary types and within [3, len(STATES)] for numeric
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
    _edges: Dict[str, Set[str]] = {}

    def add_node(self, node: str) -> ():
        self._nodes.append(node)

    def remove_node(self, node: str) -> ():
        self._nodes.remove(node)
        if node in self._edges:
            del self._edges[node]
        for v in self._edges.values():
            if node in v:
                v.remove(node)

    def add_edge(self, n1: str, n2: str, bidirectional = False) -> ():
        if n1 not in self._edges:
            self._edges[n1] = set()
        self._edges[n1].add(n2)
        if bidirectional:
            if n2 not in self._edges:
                self._edges[n2] = set()
            self._edges[n2].add(n1)

    def remove_edge(self, n1: str, n2: str, bidirectional = False) -> ():
        self._edges[n1].remove(n2)
        if bidirectional:
            self._edges[n2].remove(n1)

    def print(self) -> ():
        sys.stdout.write('Nodes: ')
        sys.stdout.write(', '.join(self._nodes))
        sys.stdout.write('\nEdges:\n')
        for n1, n2s in self._edges.items():
            for n2 in n2s:
                print(f'• {n1} -> {n2}')

    def get_nodes_like(self, pattern: str) -> List[str]:
        return list(filter(lambda x: re.match(pattern, x), self._nodes))

    def get_next_nodes(self, node: str, disregard: Optional[str] = None) -> List[str]:
        if node not in self._edges:
            return []
        return list(filter(lambda x: x is not disregard, self._edges[node]))

    def get_nodes(self) -> List[str]:
        return self._nodes


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


def get_nodes_with_state(state_graph: Graph, state: int, value: str) -> List[str]:
    '''
    Returns a list of state nodes with the given value for the given state
    '''
    return state_graph.get_nodes_like(f'^([0-9]+[A-Z]+)*{state}{value}([0-9]+[A-Z]+)*$')

def modified_state_node(node: str, state: int, value: str) -> str:
    '''
    Returns a version of the node where the given state has some other value
    '''
    before_after = re.match(f'(?:([0-9]+[A-Z]+)*){state}[A-Z]+(?:([0-9]+[A-Z]+)*)', node).groups()
    return (before_after[0] if before_after[0] else '') + f'{state}{value}' + (before_after[1] if before_after[1] else '')


def random_subset(lst: List[str]) -> List[str]:
    '''
    Returns a random subset (or at least size 1) of the input list
    '''
    results = []
    for x in lst:
        if random.randint(0,1) == 0:
            results.append(x)
    if len(results) == 0:
        results.append(lst[random.randint(0, len(lst) - 1)])
    return results


def assign_state_change_edges(state_graph: Graph, state_change: Tuple[StateChangeType, int], state: int) -> ():
    '''
    Populates edges on the state graph according to the configured state changes
    '''
    if state_change[0] == StateChangeType.BINARY_REVERSIBLE.value:
        nodes = random_subset(get_nodes_with_state(state_graph, state, 'A'))
        for node in nodes:
            state_graph.add_edge(node, modified_state_node(node, state, 'B'), True)

    if state_change[0] == StateChangeType.NUMERIC_CYCLIC.value:
        for value_index in range(state_change[1]):
            nodes = random_subset(get_nodes_with_state(state_graph, state, STATES[value_index]))
            next_value = STATES[0 if value_index + 1 == state_change[1] else value_index + 1]
            prev_value = STATES[state_change[1] - 1 if value_index == 0 else value_index - 1]
            for node in nodes:
                value = next_value if random.randint(0, 1) == 0 else prev_value
                state_graph.add_edge(node, modified_state_node(node, state, value))


def take_all_walks(state_graph: Graph, initial: str) -> Tuple[List[str], List[str]]:
    '''
    Takes all paths through the graph and returns any dead-ends (leaf nodes) as well as all visited nodes
    '''
    leaf_nodes = []
    all_nodes = []
    please_visit = [(initial, None)]
    while len(please_visit) > 0:
        node, prev = please_visit.pop(0)
        next_nodes = state_graph.get_next_nodes(node, prev)
        if len(next_nodes) == 0:
            leaf_nodes.append(node)
            continue
        unvisited_next = list(filter(lambda x: x not in all_nodes, next_nodes))
        for unvisited in unvisited_next:
            please_visit.append((unvisited, node))
            all_nodes.append(unvisited)
    return (leaf_nodes, all_nodes)


# MAIN SECTION


def generate_dungeon():
    '''
    Runs the entire algorithm to generate a dungeon
    '''
    random.seed(2020) # TODO remove this later
    config = DungeonConfig([('numeric cyclic', 3), ('binary reversible', 2)], 5, 4)

    # Create a state node for every possible combination of dungeon state (based on config values)
    state_graph = Graph()
    all_states = generate_all_states(config)
    for state in all_states:
        state_graph.add_node(state)

    # Use state change types from config to populate some edges in the state traversal graph
    for i, state_change in enumerate(config.states):
        assign_state_change_edges(state_graph, state_change, i)

    # Traverse every state node from the start, make sure the only endpoints are the final state node

    # Prune any state nodes (and their edges) that are not navigable from the initial state node
    _, all_nodes = take_all_walks(state_graph, '0A1A')
    for node in state_graph.get_nodes():
        if node not in all_nodes:
            state_graph.remove_node(node)

    # Print the state graph
    print('STATE GRAPH')
    state_graph.print()


if __name__ == '__main__':
    generate_dungeon()
