from collections import deque


class SearchLimitExceeded(TimeoutError):
    def __init__(self, nodes_expanded, max_lenstack):
        super().__init__("Przekroczono limit węzłów.")
        self.nodes_expanded = nodes_expanded
        self.max_lenstack = max_lenstack


def order_moves(moves, target_state):
    return sorted(moves, key=lambda m: m[0][1] != target_state.state[m[0][0] - 1])


def dfs_search(start_state, target_state, third_move=False, node_limit=10000, ordered=False):
    stack = [(start_state, [])]
    visited = {start_state}
    nodes_expanded = 0
    max_lenstack = len(stack)

    while stack:
        if len(stack) > max_lenstack:
            max_lenstack = len(stack)
        if nodes_expanded >= node_limit:
            raise SearchLimitExceeded(nodes_expanded, max_lenstack)

        current_state, path = stack.pop()

        if current_state == target_state:
            return path, nodes_expanded, max_lenstack

        nodes_expanded += 1

        moves = current_state.get_possible_moves(third_move=third_move)
        if ordered:
            # stos jest LIFO, więc najlepsze ruchy odkładamy na stos jako ostatnie
            moves = reversed(order_moves(moves, target_state))

        for move, next_state in moves:
            if next_state not in visited:
                visited.add(next_state)
                stack.append((next_state, path + [move]))

    return None, nodes_expanded, max_lenstack


def bfs_search(start_state, target_state, third_move=False, node_limit=10000):
    visited = {start_state}
    nodes_expanded = 0
    stack = deque()
    stack.append([start_state, []])
    max_lenstack = len(stack)
    while len(stack) > 0:
        if len(stack) > max_lenstack:
            max_lenstack = len(stack)
        if nodes_expanded >= node_limit:
            raise SearchLimitExceeded(nodes_expanded, max_lenstack)

        current_state, path = stack.popleft()

        if current_state == target_state:
            return path, nodes_expanded, max_lenstack

        nodes_expanded += 1

        for move, next_state in current_state.get_possible_moves(third_move=third_move):
            if next_state not in visited:
                visited.add(next_state)
                stack.append([next_state, path + [move]])

    return None, nodes_expanded, max_lenstack