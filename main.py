from sys import argv
from parser import parse_block_file
from random_state_generator import generate_state
from state import BlocksState
from solver import dfs_search, bfs_search
from verify import verify_sequence

start_state, target_state = parse_block_file("test1.txt")

start_obj = BlocksState(start_state)
target_obj = BlocksState(target_state)

# dfs
path, nodes_extended = dfs_search(start_obj, target_obj)
print("===dfs===")
print(f"sekwencja:  {path}")
print(f"ilość ruchów:  {len(path)}")
print(f"przeszukanych węzłów: {nodes_extended}")
# dfs 3moves
path, nodes_extended = dfs_search(start_obj, target_obj, True)
print("===dfs 3 moves===")
print(f"sekwencja:  {path}")
print(f"ilość ruchów:  {len(path)}")
print(f"przeszukanych węzłów: {nodes_extended}")

# bfs
path, nodes_extended = bfs_search(start_obj, target_obj, )
print("===bfs===")
print(f"sekwencja:  {path}")
print(f"ilość ruchów:  {len(path)}")
print(f"przeszukanych węzłów: {nodes_extended}")
#bfs 3moves
path, nodes_extended = bfs_search(start_obj, target_obj, True)
print("===bfs 3 moves===")
print(f"sekwencja:  {path}")
print(f"ilość ruchów:  {len(path)}")
print(f"przeszukanych węzłów: {nodes_extended}")

# tescik
start_obj = generate_state(6, 7)
target_obj = generate_state(6, 9)
path, nodes_extended = bfs_search(start_obj, target_obj, True, 1000000)

verify_sequence(start_obj, target_obj, path, True)