'''
This module implements the dungeon generation algorithm
'''
import sys
import copy
import random
from typing import List, Tuple, Dict, Set, Optional, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum

# Terms:
# • State is some variable (binary or numerical) that affects your progression through the dungeon
# • Total state is the sum of all states in the dungeon
# • Value is one of several possibilities that a state can be in at a given time
# • State type describes how a state can change with respect to the player's position in the dungeon
#
# Set up state graph:
# • Read input config to get types of state change and final state(s)
# • Calculate all possible states and create nodes for them
# • Use the types of state change to add edges to the state nodes
# • Make sure all state paths converge upon a final state
# • Prune disconnected state nodes
#
# Generate dungeon layout:
# • Create W x H rooms (nodes) and generate an enclave for each unique state change + 1
#   (final room's enclave)
# • Assign each enclave (minus the last one) to some state change
# • At each state node, connect the enclave represented by its edges to the enclave(s)
#   represented by the connected state node's edges with a conditional passage
# • Throw in some one-way doors to "earlier" enclaves (based on state graph path traversal order)


# TYPES AND CONSTANTS SECTION


class TotalState:
    '''
    Records values for each state
    '''
    _values: List[int]

    def __init__(self, n: int):
        self._values = [0 for _ in range(n)]

    def set(self, index: int, value: int):
        self._values[index] = value

    def get(self, index: int) -> int:
        return self._values[index]

    def inc(self, index: int):
        self._values[index] = self._values[index] + 1

    def __str__(self):
        content = ', '.join(list(map(str, self._values)))
        return f'({content})'

    def __eq__(self, x):
        return str(self) == str(x)

    def __hash__(self):
        return hash(str(self))


class StateType(Enum):
    '''
    Defines the canonical state types that this algorithm can process
    '''
    BINARY_REVERSIBLE = 'binary reversible'
    BINARY_IRREVERSIBLE = 'binary irreversible'
    BINARY_CYCLIC = 'binary cyclic'
    NUMERIC_OPTIONAL = 'numeric optional'
    NUMERIC_IRREVERSIBLE = 'numeric irreversible'
    NUMERIC_CYCLIC = 'numeric cyclic'


@dataclass
class State:
    '''
    Represents dungeon state
    '''
    state_type: StateType
    values: int
    # NOTE values must be 2 if the state type is binary and within [3, 8] otherwise


@dataclass
class DungeonConfig:
    '''
    Represents some input config when generating a dungeon
    '''
    states: List[State]
    w: int # Width of the rooms rectangle
    h: int # Height of the rooms rectangle


G = TypeVar('G')
class Graph(Generic[G]):
    '''
    Abstraction for a graph
    '''
    _nodes: List[G] = []
    _edges: Dict[G, Set[G]] = {}

    def add_node(self, node: G) -> ():
        self._nodes.append(node)

    def remove_node(self, node: G) -> ():
        self._nodes.remove(node)
        if node in self._edges:
            del self._edges[node]
        for v in self._edges.values():
            if node in v:
                v.remove(node)

    def add_edge(self, n1: G, n2: G, bidirectional = False) -> ():
        if n1 not in self._edges:
            self._edges[n1] = set()
        self._edges[n1].add(n2)
        if bidirectional:
            if n2 not in self._edges:
                self._edges[n2] = set()
            self._edges[n2].add(n1)

    def remove_edge(self, n1: G, n2: G, bidirectional = False) -> ():
        self._edges[n1].remove(n2)
        if bidirectional:
            self._edges[n2].remove(n1)

    def print(self) -> ():
        sys.stdout.write('Nodes: ')
        sys.stdout.write(', '.join(list(map(str, self._nodes))))
        sys.stdout.write('\nEdges:\n')
        for n1, n2s in self._edges.items():
            for n2 in n2s:
                print(f'• {n1} -> {n2}')

    def get_next_nodes(self, node: G, disregard: Optional[G] = None) -> List[G]:
        if node not in self._edges:
            return []
        return list(filter(lambda x: x is not disregard, self._edges[node]))

    def get_nodes(self) -> List[G]:
        return self._nodes


# GENERATE STATE GRAPH SECTION


def generate_all_total_states(config: DungeonConfig) -> List[TotalState]:
    '''
    Generates all possibilities for total state by the config
    '''
    results = []
    total_state = TotalState(len(config.states))
    done = False
    while not done:
        results.append(total_state)
        a = 0
        total_state = copy.deepcopy(total_state)
        while True:
            total_state.inc(a)
            if total_state.get(a) == config.states[a].values:
                total_state.set(a, 0)
                a += 1
                if a == len(config.states):
                    done = True
                    break
                continue
            break
    return results


def get_nodes_with_state_and_value(state_graph: Graph, state: int, value: int) -> List[TotalState]:
    '''
    Returns a list of state nodes with the given value for the given state
    '''
    return list(filter(lambda x: x.get(state) == value, state_graph.get_nodes()))

def modified_state_node(node: TotalState, state: int, value: int) -> TotalState:
    '''
    Returns a version of the node where the given state has some other value
    '''
    modified = copy.deepcopy(node)
    modified.set(state, value)
    return modified


def random_subset(lst: List) -> List:
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


def assign_state_change_edges(state_graph: Graph, state: Tuple[StateType, int], state_index: int) -> ():
    '''
    Populates edges on the state graph according to the configured state changes
    '''
    if state.state_type == StateType.BINARY_REVERSIBLE.value:
        nodes = random_subset(get_nodes_with_state_and_value(state_graph, state_index, 0))
        for node in nodes:
            state_graph.add_edge(node, modified_state_node(node, state_index, 1), True)

    if state.state_type == StateType.NUMERIC_CYCLIC.value:
        for value in range(state.values):
            nodes = random_subset(get_nodes_with_state_and_value(state_graph, state_index, value))
            next_value = 0 if value + 1 == state.values else value + 1
            prev_value = state.values - 1 if value == 0 else value - 1
            for node in nodes:
                new_value = next_value if random.randint(0, 1) == 0 else prev_value
                state_graph.add_edge(node, modified_state_node(node, state_index, new_value))


T = TypeVar('T')
def take_all_walks(state_graph: Graph, initial: T) -> Tuple[List[T], List[T]]:
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
    config = DungeonConfig([State('numeric cyclic', 3), State('binary reversible', 2)], 5, 4)

    # Create a state node for every possible combination of dungeon state (based on config values)
    state_graph = Graph()
    all_states = generate_all_total_states(config)
    for state in all_states:
        state_graph.add_node(state)

    # Use state change types from config to populate some edges in the state traversal graph
    for i, state_change in enumerate(config.states):
        assign_state_change_edges(state_graph, state_change, i)

    # Traverse every state node from the start, make sure the only endpoints are the final state node

    # Prune any state nodes (and their edges) that are not navigable from the initial state node
    _, all_nodes = take_all_walks(state_graph, state_graph.get_nodes()[0])
    for node in state_graph.get_nodes():
        if node not in all_nodes:
            state_graph.remove_node(node)

    # Print the state graph
    print('STATE GRAPH')
    state_graph.print()


if __name__ == '__main__':
    generate_dungeon()
