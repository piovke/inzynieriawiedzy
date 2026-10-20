from collections import deque


# Porządkowanie ruchów: ruchy, które kładą klocek od razu na jego miejscu z układu docelowego,
# są rozpatrywane jako pierwsze. Pozostałe zachowują kolejność z generatora (sortowanie jest stabilne).
def order_moves(moves, target_state):
    return sorted(moves, key=lambda m: m[0][1] != target_state.state[m[0][0] - 1])


# Funkcja implementująca algorytm DFS z backtrackingiem do rozwiązania problemu, jako argumenty przyjmuje tablicę
# z układem początkowym i docelowym, limit węzłów oraz opcję porządkowania ruchów (ordered).
def dfs_search(start_state, target_state, third_move=False, node_limit=10000, ordered=False):
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

        moves = current_state.get_possible_moves(third_move=third_move)
        if ordered:
            # stos jest LIFO, więc najlepsze ruchy odkładamy na stos jako ostatnie
            moves = reversed(order_moves(moves, target_state))

        for move, next_state in moves:
            if next_state not in visited:
                visited.add(next_state)
                stack.append((next_state, path + [move]))

    return None, nodes_expanded


def bfs_search(start_state, target_state, third_move=False, node_limit=10000):
    visited = {start_state}
    nodes_expanded = 0
    stack = deque()
    stack.append([start_state, []])

    while len(stack) > 0:
        if nodes_expanded >= node_limit:
            raise TimeoutError("Przekroczono limit węzłów.")

        current_state, path = stack.popleft()

        if current_state == target_state:
            return path, nodes_expanded

        nodes_expanded += 1

        for move, next_state in current_state.get_possible_moves(third_move=third_move):
            if next_state not in visited:
                visited.add(next_state)
                stack.append([next_state, path + [move]])

    return None, nodes_expanded