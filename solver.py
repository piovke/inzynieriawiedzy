# Funkcja implementująca algorytm DFS z backtrackingiem do rozwiązania problemu, jako argumenty przyjmuje tablicę
# z układem początkowym i docelowym oraz limit węzłów.
def dfs_search(start_state, target_state, node_limit=10000):
    stack = [(start_state, [])]
    visited = {start_state}
    nodes_expanded = 0

    while stack:
        if nodes_expanded >= node_limit:
            raise TimeoutError("Przekroczono limit węzłów.")

        current_state, path = stack.pop()

        if current_state == target_state:
            return path, nodes_expanded

        nodes_expanded += 1

        for move, next_state in current_state.get_possible_moves():
            if next_state not in visited:
                visited.add(next_state)
                stack.append((next_state, path + [move]))

    return None, nodes_expanded
