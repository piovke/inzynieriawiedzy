from sys import argv
from parser import parse_block_file
from state import BlocksState
from solver import dfs_search

start_state, target_state = parse_block_file(argv[1])

start_obj = BlocksState(start_state)
target_obj = BlocksState(target_state)

path, nodes_extended = dfs_search(start_obj, target_obj)

print(path)
print(nodes_extended)