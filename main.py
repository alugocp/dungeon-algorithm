'''
This module implements the dungeon generation algorithm
'''
import sys
import math
import copy
import random
from typing import List, Tuple, Dict, Set, TypeVar, Generic
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
        return ''.join(list(map(str, self._values)))

    def __eq__(self, x):
        return str(self) == str(x)

    def __hash__(self):
        return hash(str(self))


@dataclass
class TotalStateDelta():
    '''
    Recdords the difference between two total states
    '''
    state_index: int # Index of the changed state
    value1: int # The value before the change
    value2: int # the value after the change
    omnidirectional: bool

    def __str__(self):
        return f'{self.state_index}:*' \
            if self.omnidirectional \
            else f'{self.state_index}:{self.value1}->{self.value2}'

    def __eq__(self, x):
        return str(self) == str(x)

    def __hash__(self):
        return hash(str(self))

class Enclave:
    '''
    Represents an enclave in the dungeon
    '''
    delta: TotalStateDelta
    nodes: List[int]

    def __init__(self, node: int):
        self.delta = None
        self.nodes = [node]

    def __str__(self):
        nodes = ', '.join(list(map(str, self.nodes)))
        return f'{self.delta} ({nodes})'


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
    _nodes: List[G]
    _edges: Dict[G, Set[G]]

    def __init__(self):
        self._nodes = []
        self._edges = {}

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

    def is_bidirectional(self, n1: G, n2: G) -> bool:
        return n1 in self._edges and n2 in self._edges and \
            n2 in self._edges[n1] and n1 in self._edges[n2]

    def print(self) -> ():
        sys.stdout.write('Nodes: ')
        sys.stdout.write(', '.join(list(map(str, self._nodes))))
        sys.stdout.write('\nEdges:\n')
        edge_logs = []
        for n1, n2s in self._edges.items():
            for n2 in n2s:
                opposite = f'• {n2} -- {n1}'
                if not self.is_bidirectional(n1, n2):
                    edge_logs.append(f'• {n1} -> {n2}')
                elif opposite not in edge_logs:
                    edge_logs.append(f'• {n1} -- {n2}')
        edge_logs.sort()
        for edge in edge_logs:
            print(edge)

    def get_next_nodes(self, node: G) -> List[G]:
        if node not in self._edges:
            return []
        return list(self._edges[node])

    def get_nodes(self) -> List[G]:
        return self._nodes

    def get_edges(self) -> List[Tuple[G, G]]:
        edges = []
        for n1, n2s in self._edges.items():
            for n2 in n2s:
                edges.append((n1, n2))
        return edges


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


def assign_state_change_edges(
    state_graph: Graph,
    state: Tuple[StateType, int],
    state_index: int
) -> ():
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
    Takes all paths through the graph and returns any
    dead-ends (leaf nodes) as well as all visited nodes
    '''
    leaf_nodes = []
    all_nodes = [initial]
    please_visit = [(initial, None)]
    while len(please_visit) > 0:
        node, prev = please_visit.pop(0)
        next_nodes = state_graph.get_next_nodes(node)
        if len(next_nodes) == 0 or (len(next_nodes) == 1 and prev in next_nodes):
            leaf_nodes.append(node)
            continue
        unvisited_next = list(filter(lambda x: x not in all_nodes, next_nodes))
        for unvisited in unvisited_next:
            please_visit.append((unvisited, node))
            all_nodes.append(unvisited)
    return (leaf_nodes, all_nodes)

def get_total_state_delta(config: DungeonConfig, t1: TotalState, t2: TotalState) -> TotalStateDelta:
    '''
    Returns a total state delta object derived from the difference between two total states
    '''
    diff = -1
    for a in range(len(config.states)):
        if t1.get(a) != t2.get(a):
            if diff > -1:
                raise RuntimeError('Total states have more than one difference')
            diff = a
    if diff == -1:
        raise RuntimeError('Total states are the exact same')
    omnidirectional = config.states[diff].state_type in [
        StateType.BINARY_REVERSIBLE.value,
        StateType.NUMERIC_OPTIONAL.value
    ]
    return TotalStateDelta(diff, t1.get(diff), t2.get(diff), omnidirectional)

def get_all_total_state_deltas(state_graph: Graph, config: DungeonConfig) -> List[TotalStateDelta]:
    '''
    Returns a list of all unique total state deltas present in the state graph
    '''
    deltas = set()
    for n1, n2 in state_graph.get_edges():
        deltas.add(get_total_state_delta(config, n1, n2))
    return list(deltas)


# GENERATE DUNGEON GRAPH SECTION


def get_room_node_names(w: int, h: int) -> List[int]:
    '''
    Generates a list of names for w * h room graph nodes
    '''
    return list(range(w * h))


def get_adjacent_rooms(room: int, w: int, h: int) -> List[int]:
    '''
    Returns the adjacent nodes of some room in the room graph
    '''
    neighbors = []
    x = room % w
    y = math.floor(room / w)
    if x > 0:
        neighbors.append(room - 1)
    if x < w - 1:
        neighbors.append(room + 1)
    if y > 0:
        neighbors.append(room - w)
    if y < h - 1:
        neighbors.append(room + w)
    return neighbors


def make_enclaves(room_graph: Graph, n: int, w: int, h: int) -> List[Enclave]:
    '''
    Assigns edges such that the room graph contains n non-cyclic
    paths that cover the entire graph but do not intersect
    '''
    enclaves = []
    all_nodes = copy.deepcopy(room_graph.get_nodes())
    process_next = []
    visited = []
    def unvisited_and_unqueued(x):
        return x not in visited and x not in process_next

    # Grab n random nodes to seed the enclaves
    for _ in range(n):
        node = all_nodes.pop(random.randint(0, len(all_nodes) - 1))
        enclaves.append(Enclave(node))
        visited.append(node)

    # Add each enclave seed's unvisited and unqueued neighbors to the queue
    for node in visited:
        next_in_queue = list(filter(
            unvisited_and_unqueued,
            get_adjacent_rooms(node, w, h)
        ))
        process_next += next_in_queue

    # Process the queue to put every node in an enclave
    while len(process_next) > 0:
        node = process_next.pop(0)

        # Add a bidirectional edge from this node to one of its visited neighbors
        options = list(filter(
            lambda x: x in visited,
            get_adjacent_rooms(node, w, h)
        ))
        if len(options) > 0:
            node1 = options[random.randint(0, len(options) - 1)]
            room_graph.add_edge(node, node1, True)

            # Find the enclave this neighbor belongs to and add the node to it
            enclave = list(filter(lambda x: node1 in x.nodes, enclaves))[0]
            enclave.nodes.append(node)

        # Add the node to the visited set
        visited.append(node)

        # Add its unvisited and unqueued neighbors to the queue
        next_in_queue = list(filter(
            unvisited_and_unqueued,
            get_adjacent_rooms(node, w, h)
        ))
        process_next += next_in_queue
    enclaves.sort(key = lambda e: len(e.nodes), reverse = True)
    return enclaves

# TODO does this algortithm work if there are multiple edges coming from a state node?
#      Review with more complicated state graphs, and perhaps rework state graph generation
#      to only generate a single non-branching path.
def get_deltas_required_by_total_state(config: DungeonConfig, state_graph: Graph, final_nodes: List[int]) -> ():
    '''
    Traverses through the state graph and returns all the total state
    deltas that must be accessible at each total state node
    '''
    first_enclave = None
    visited = []
    queued = [ (None, state_graph.get_nodes()[0]) ]
    while len(queued) > 0:
        prev, node = queued.pop(0)
        visited.append((prev, node))
        if node in final_nodes:
            prev_delta = get_total_state_delta(config, prev, node)
            print(f'• Enclave {prev_delta} -- final enclave when {node}')
        for node1 in state_graph.get_next_nodes(node):
            # Retrieve the total state delta (enclave) between
            # the current total state and the next total state
            delta = get_total_state_delta(config, node, node1)
            # TODO we may need to create a set of first enclaves
            #      for each edge from the initial state node
            if first_enclave is None:
                first_enclave = delta
                print(f'• First enclave is {delta}')
            if prev is not None:
                # Retrieve the previous state delta (state graph edge /
                # total state delta / enclave that came before the currently
                # considered one) so we can establish a conditional path
                # between two enclaves dependent on the total state they share.
                prev_delta = get_total_state_delta(config, prev, node)
                if delta != prev_delta:
                    print(f'• Enclave {prev_delta} -- enclave {delta} when {node}')

            # Next we should check the edge from node -> node1
            please_queue = (node, node1)
            if please_queue not in visited and please_queue not in queued:
                queued.append((node, node1))


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

    # Get the initial and final state nodes
    initial_node = state_graph.get_nodes()[0]
    final_nodes = list(filter(lambda x: str(x) in ['21'], state_graph.get_nodes()))

    # Prune any state nodes (and their edges) that are not navigable from the initial state node
    leaf_nodes, all_nodes = take_all_walks(state_graph, initial_node)
    for node in state_graph.get_nodes():
        if node not in all_nodes:
            state_graph.remove_node(node)

    # Prune any leaf nodes that aren't part the final total state
    nodes_to_prune = list(filter(lambda x: x not in final_nodes, leaf_nodes))
    while len(nodes_to_prune) > 0:
        for node in nodes_to_prune:
            state_graph.remove_node(node)
        leaf_nodes, _ = take_all_walks(state_graph, initial_node)
        nodes_to_prune = list(filter(lambda x: x not in final_nodes, leaf_nodes))

    # TODO double check that the initial node has a path to some final
    #      node and fix that if it doesn't

    total_state_deltas = get_all_total_state_deltas(state_graph, config)

    # Print the state graph
    print('STATE GRAPH')
    state_graph.print()
    print('')

    # Create a room graph with all the room names as nodes
    room_graph = Graph()
    for room in get_room_node_names(config.w, config.h):
        room_graph.add_node(room)

    # Generate enclaves in the room graph (1 for each unique total state delta
    # plus the final enclave) and assign total state deltas to them
    enclaves = make_enclaves(room_graph, len(total_state_deltas) + 1, config.w, config.h)
    for a, delta in enumerate(total_state_deltas):
        # TODO deltas are assigned to enclaves basically at random. This is fine
        #      except for the first state delta/enclave, which must be determined
        #      by the result of get_deltas_required_by_total_state()
        enclaves[a].delta = delta

    # Print the room graph
    print('ROOM GRAPH')
    room_graph.print()

    # TODO print for debugging
    print(list(map(str, enclaves)))
    get_deltas_required_by_total_state(config, state_graph, final_nodes)


if __name__ == '__main__':
    generate_dungeon()
