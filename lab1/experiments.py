import time
from functools import partial
from random_state_generator import generate_state
from solver import dfs_search, bfs_search, SearchLimitExceeded
from verify import verify_sequence

dfs_ordered = partial(dfs_search, ordered=True)

SEED = 2024
THIRD_MOVE = True
LIMIT = 200000


def run(search, start, target, third_move):
    t = time.perf_counter()
    try:
        path, nodes, max_lenstack = search(start, target, third_move, LIMIT)
    except SearchLimitExceeded as error:
        return None, error.nodes_expanded, time.perf_counter() - t, error.max_lenstack
    return path, nodes, time.perf_counter() - t, max_lenstack


# dfs
for n in range(3, 10):
    for i in range(5):
        start = generate_state(n, SEED + 1000 * n + 10 * i)
        target = generate_state(n, SEED + 1000 * n + 10 * i + 1)
        path, nodes, dt, max_lenstack = run(dfs_ordered, start, target, THIRD_MOVE)

        print(f"N={n} #{i + 1}: start={start.state} cel={target.state}")
        if path is None:
            print(f"  przekroczono limit, węzłów: {nodes}, maks. stos: {max_lenstack}, czas: {dt:.3f}s")
            continue
        print(f"  ruchów: {len(path)}, węzłów: {nodes}, maks. stos: {max_lenstack}, czas: {dt:.3f}s")
        if n <= 8:
            print(f"  sekwencja: {path}")
        verify_sequence(start, target, path, THIRD_MOVE)


# dfs vs bfs
print("\n=== DFS vs BFS, N=8, 3 ruchy ===")
sums = {"dfs": [0, 0, 0.0, 0, 0], "bfs": [0, 0, 0.0, 0, 0]}  # ruchy, węzły, czas, maks. stos, liczba rozwiązanych
for i in range(10):
    start = generate_state(8, SEED + 50000 + 10 * i)
    target = generate_state(8, SEED + 50000 + 10 * i + 1)
    for name, search in (("dfs", dfs_ordered), ("bfs", bfs_search)):
        path, nodes, dt, max_lenstack = run(search, start, target, True)
        if path is None:
            print(f"#{i + 1} {name}: limit, węzłów: {nodes}, maks. stos: {max_lenstack}, czas: {dt:.3f}s")
            continue
        print(f"#{i + 1} {name}: ruchów: {len(path)}, węzłów: {nodes}, maks. stos: {max_lenstack}, czas: {dt:.3f}s")
        s = sums[name]
        s[0] += len(path)
        s[1] += nodes
        s[2] += dt
        s[3] += max_lenstack
        s[4] += 1

for name, (moves, nodes, dt, max_lenstack, k) in sums.items():
    if k:
        print(
            f"średnio {name} ({k}/10): ruchów {moves / k:.1f}, węzłów {nodes / k:.1f}, "
            f"maks. stos {max_lenstack / k:.1f}, czas {dt / k:.3f}s"
        )