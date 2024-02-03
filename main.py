'''
This module implements the dungeon generation algorithm
'''
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
    w: int # Width of the rooms rectangle
    h: int # Height of the rooms rectangle
