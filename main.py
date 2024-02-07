'''
This module implements the dungeon generation algorithm
'''
import sys
import math
import copy
import json
import random
from typing import List, Tuple, Dict, Set, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import jsonschema

# TYPES AND CONSTANTS SECTION

class TotalState:
    '''
    Records values for each state
    '''
    _values: List[int]

    def __init__(self, n: int):
        self._values = [0 for _ in range(n)]

    @staticmethod
    def from_list(ls: List[int]):
        '''
        Instantiates a new TotalState with some list for the values
        '''
        ts = TotalState(len(ls))
        for i, val in enumerate(ls):
            ts.set(i, val)
        return ts

    def set(self, index: int, value: int):
        '''
        Sets the value at index
        '''
        self._values[index] = value

    def get(self, index: int) -> int:
        '''
        Gets the value at index
        '''
        return self._values[index]

    def inc(self, index: int):
        '''
        Increments the value at index
        '''
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
    Records the difference between two total states
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
        label = self.delta or 'Final'
        return f'{label} ({nodes})'

class StateType(Enum):
    '''
    Defines the canonical state types that this algorithm can process
    '''
    BINARY_REVERSIBLE = 'binary reversible'
    BINARY_IRREVERSIBLE = 'binary irreversible'
    BINARY_CYCLIC = 'binary cyclic'
    NUMERIC_REVERSIBLE = 'numeric reversible'
    NUMERIC_CYCLIC = 'numeric cyclic'

@dataclass
class State:
    '''
    Represents dungeon state
    '''
    state_type: StateType
    values: int

@dataclass
class DungeonConfig:
    '''
    Represents some input config when generating a dungeon
    '''
    w: int # Width of the rooms rectangle
    h: int # Height of the rooms rectangle
    states: List[State]
    final_total_states: List[TotalState]

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
        '''
        Add a node to the graph
        '''
        self._nodes.append(node)

    def remove_node(self, node: G) -> ():
        '''
        Remove a node and its edges from the graph
        '''
        self._nodes.remove(node)
        if node in self._edges:
            del self._edges[node]
        for v in self._edges.values():
            if node in v:
                v.remove(node)

    def has_node(self, node: G) -> bool:
        '''
        Returns True if this graph contains the node in question
        '''
        return node in self._nodes

    def add_edge(self, n1: G, n2: G, bidirectional = False) -> ():
        '''
        Add an edge between two nodes in this graph (optional bidirectionality)
        '''
        if n1 not in self._edges:
            self._edges[n1] = set()
        self._edges[n1].add(n2)
        if bidirectional:
            if n2 not in self._edges:
                self._edges[n2] = set()
            self._edges[n2].add(n1)

    def remove_edge(self, n1: G, n2: G, bidirectional = False) -> ():
        '''
        Remove an edge between two nodes in the graph (optional bidirectionality)
        '''
        self._edges[n1].remove(n2)
        if bidirectional:
            self._edges[n2].remove(n1)

    def is_bidirectional(self, n1: G, n2: G) -> bool:
        '''
        Returns True if the edge between these two nodes is bidirectional
        '''
        return n1 in self._edges and n2 in self._edges and \
            n2 in self._edges[n1] and n1 in self._edges[n2]

    def print(self) -> ():
        '''
        Prints all nodes and edges in this graph (differentiates for bidirectionality)
        '''
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
        '''
        Returns all nodes that the given node points to
        '''
        if node not in self._edges:
            return []
        return list(self._edges[node])

    def get_nodes(self) -> List[G]:
        '''
        Return all nodes in this graph
        '''
        return self._nodes

    def get_edges(self) -> List[Tuple[G, G]]:
        '''
        Returns a node tuple for every edge in this graph
        '''
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

def assign_state_change_edges(
    state_graph: Graph,
    state: Tuple[StateType, int],
    state_index: int
) -> ():
    '''
    Populates edges on the state graph according to the configured state changes
    '''
    # Binary state that can the player can switch back and forth at will
    if state.state_type == StateType.BINARY_REVERSIBLE.value:
        nodes = get_nodes_with_state_and_value(state_graph, state_index, 0)
        for node in nodes:
            state_graph.add_edge(node, modified_state_node(node, state_index, 1), True)

    # Binary state that the player can only change in one direction at a time
    if state.state_type == StateType.BINARY_CYCLIC.value:
        nodes = get_nodes_with_state_and_value(state_graph, state_index, 0)
        for node in nodes:
            state_graph.add_edge(node, modified_state_node(node, state_index, 1))

        nodes = get_nodes_with_state_and_value(state_graph, state_index, 1)
        for node in nodes:
            state_graph.add_edge(node, modified_state_node(node, state_index, 0))

    # Binary state with no way to change back
    if state.state_type == StateType.BINARY_IRREVERSIBLE.value:
        nodes = get_nodes_with_state_and_value(state_graph, state_index, 0)
        for node in nodes:
            state_graph.add_edge(node, modified_state_node(node, state_index, 1))

    # Nonbinary state that can the player can alter at will
    if state.state_type == StateType.NUMERIC_REVERSIBLE.value:
        nodes = get_nodes_with_state_and_value(state_graph, state_index, 0)
        for node in nodes:
            for value in range(state.values - 1):
                for value1 in range(value + 1, state.values):
                    state_graph.add_edge(
                        modified_state_node(node, state_index, value),
                        modified_state_node(node, state_index, value1),
                        True
                    )

    # Nonbinary state that the player can only change in one direction at a time
    if state.state_type == StateType.NUMERIC_CYCLIC.value:
        for value in range(state.values):
            nodes = get_nodes_with_state_and_value(state_graph, state_index, value)
            next_value = 0 if value + 1 == state.values else value + 1
            for node in nodes:
                state_graph.add_edge(node, modified_state_node(node, state_index, next_value))

def generate_state_graph(config: DungeonConfig) -> Graph:
    '''
    Generates a state graph by taking a random walk through the
    "proto" state graph (made up of all total states and the edges
    between them based on state in the dungeon config)
    '''
    state_graph = Graph()

    # Populate the proto state graph from all possible total states
    proto_graph = Graph()
    for state in generate_all_total_states(config):
        proto_graph.add_node(state)

    # Use state types from config to populate some edges in the proto state graph
    for i, state_change in enumerate(config.states):
        assign_state_change_edges(proto_graph, state_change, i)

    # Populate the state graph as a random walk through the proto graph
    node = proto_graph.get_nodes()[0]
    state_graph.add_node(node)
    while node not in config.final_total_states:
        next_nodes = list(filter(
            lambda x: not state_graph.has_node(x),
            proto_graph.get_next_nodes(node)
        ))
        if len(next_nodes) == 0:
            raise RuntimeError('Did not find path to a final total state node')
        node1 = next_nodes[random.randint(0, len(next_nodes) - 1)]
        state_graph.add_node(node1)
        state_graph.add_edge(node, node1, proto_graph.is_bidirectional(node, node1))
        node = node1
    return state_graph

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
        StateType.NUMERIC_REVERSIBLE.value
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

def walk_state_graph_and_connect_enclaves(config: DungeonConfig, state_graph: Graph) -> ():
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
        if node in config.final_total_states:
            prev_delta = get_total_state_delta(config, prev, node)
            print(f'• Enclave {prev_delta} -- final enclave when {node}')

        for node1 in state_graph.get_next_nodes(node):
            # Retrieve the total state delta (enclave) between
            # the current total state and the next total state
            delta = get_total_state_delta(config, node, node1)

            # If we're coming from the first state node (prev is None) then every
            # edge (enclave) here should be navigable from the first enclave and
            # one of them should actually be the first enclave.
            if prev is None:
                if first_enclave is None:
                    first_enclave = delta
                    print(f'• First enclave is {delta}')
                else:
                    print(f'• Enclave {first_enclave} -- enclave {delta} when {node}')
            else:
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

def load_config(filepath: str) -> DungeonConfig:
    '''
    Loads and validates dungeon configuration from a JSON file
    '''
    schema = {
        'type': 'object',
        'properties': {
            'width': { 'type': 'number' },
            'height': { 'type': 'number' },
            'state': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'type': { 'enum': [ x.value for x in  StateType ] },
                        'values': { 'type': 'number' }
                    }
                }
            },
            'final_total_state': {
                'type': 'array',
                'items': { 'type': 'number' }
            }
        }
    }

    # Open JSON file and validate the schema
    with open(filepath, 'r', encoding = 'utf-8') as file:
        data = json.loads(file.read())
    jsonschema.validate(instance = data, schema = schema)

    # Validate a few other details
    for state in data['state']:
        if 'binary' in state['type'] and state['values'] != 2:
            raise RuntimeError('Invalid config: binary states can only have 2 values')
        if 'numeric' in state['type'] and state['values'] < 3:
            raise RuntimeError('Invalid config: numeric states must have at least 3 values')

    if len(data['state']) != len(data['final_total_state']):
        raise RuntimeError('Invalid config: final_total_state must contain a value for every entry in state')

    for i, value in enumerate(data['final_total_state']):
        if value >= data['state'][i]['values']:
            raise RuntimeError('Invalid config: each entry in final_total_config must be <= the corresponding state\'s values field')

    return DungeonConfig(
        data['width'],
        data['height'],
        list(map(lambda x: State(x['type'], x['values']), data['state'])),
        [TotalState.from_list(data['final_total_state'])]
    )

def generate_dungeon():
    '''
    Runs the entire algorithm to generate a dungeon
    '''
    if len(sys.argv) < 2:
        raise RuntimeError('Too few command line arguments')
    config = load_config(sys.argv[1])

    # Get the state graph and extract unique total state deltas from its edges
    state_graph = generate_state_graph(config)
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
        enclaves[a].delta = delta

    # Print the room graph
    print('ROOM GRAPH')
    room_graph.print()
    print('')

    print('ENCLAVES')
    for enclave in enclaves:
        print(f'• {enclave}')
    print('')

    print('ENCLAVE TRAVERSAL')
    walk_state_graph_and_connect_enclaves(config, state_graph)

if __name__ == '__main__':
    generate_dungeon()
