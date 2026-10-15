from sys import argv
from parser import parse_block_file
from state import BlocksState
from solver import dfs_search, bfs_search

start_state, target_state = parse_block_file("test1.txt")

start_obj = BlocksState(start_state)
target_obj = BlocksState(target_state)

# dfs
path, nodes_extended = dfs_search(start_obj, target_obj)
print("===dfs===")
print(f"sekwencja:  {path}")
print(f"ilość ruchów:  {len(path)}")
print(f"przeszukanych węzłów: {nodes_extended}")

# bfs
path, nodes_extended = bfs_search(start_obj, target_obj)
print("===bfs===")
print(f"sekwencja:  {path}")
print(f"ilość ruchów:  {len(path)}")
print(f"przeszukanych węzłów: {nodes_extended}")