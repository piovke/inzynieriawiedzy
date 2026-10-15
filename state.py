from collections import Counter

# Klasa opisująca stan klocków w układzie
class BlocksState:
    def __init__(self, state_sequence):
        self.state = tuple(state_sequence)
        self.n = len(self.state)
        self._validate()


    # Metoda sprawdzająca czy układ jest poprawny
    def _validate(self):

        # Czy wszystkie klocki leżą na istniejącym podłożu?
        for x in self.state:
            if x < 0 or x > self.n:
                raise ValueError(f"Błąd walidacji: Klocek leży na nieistniejącym podłożu {x}.")

        # Czy klocki nie leżą na samych sobie?
        for i, support in enumerate(self.state):
            if support == i + 1:
                raise ValueError(f"Błąd walidacji: Klocek {i+1} leży na samym sobie.")

        # Czy na jednym klocku leży więcej niż jeden klocek?
        counts = Counter(x for x in self.state if x != 0)
        for support, count in counts.items():
            if count > 1:
                raise ValueError(f"Błąd walidacji: Na klocku {support} leży więcej niż jeden klocek.")

        # Czy klocki leżą na sobie nawzajem (zapętlają się)?
        for i in range(1, self.n + 1):
            visited_in_path = set()
            curr = i
            while curr != 0:
                if curr in visited_in_path:
                    raise ValueError(f"Błąd walidacji: Cykl w układzie (zaczęto od {i}, zapętlono na {curr}).")
                visited_in_path.add(curr)
                curr = self.state[curr - 1]


    # Metoda zwracająca tablicę wszystkich wolnych klocków (można je podnieść).
    def get_free_blocks(self):
        supporting_blocks = set(self.state)
        return [i for i in range(1, self.n + 1) if i not in supporting_blocks]


    # Metoda zwracająca tablicę wszystkich możliwych ruchów na układzie.
    def get_possible_moves(self, third_move=False):
        moves = []
        free_blocks = self.get_free_blocks()

        # 3 dostępne ruchy
        if third_move:
            for block in free_blocks:
                support = self.state[block - 1]
                # Klocki ze stołu można przełożyć tylko na inne klocki
                if support == 0:
                    for target in free_blocks:
                        if target != block:
                            new_state_list = list(self.state)
                            new_state_list[block - 1] = target

                            new_state_obj = BlocksState(new_state_list)
                            moves.append(((block, target), new_state_obj))

                # Klocki z innych klocków można przełożyć i na klocki i na stół
                else:
                    for target in free_blocks:
                        if target != block:
                            new_state_list = list(self.state)
                            new_state_list[block - 1] = target

                            new_state_obj = BlocksState(new_state_list)
                            moves.append(((block, target), new_state_obj))

                    # na stół
                    new_state_list = list(self.state)
                    new_state_list[block - 1] = 0
                    new_state_obj = BlocksState(new_state_list)
                    moves.append(((block, 0), new_state_obj))

        # 2 dostępne ruchy
        else:
            # Sprawdzamy każdy wolny klocek
            for block in free_blocks:
                support = self.state[block - 1]

                # Jeśli klocek leży na innym klocku, można przełożyć go na stół
                if support != 0:
                    new_state_list = list(self.state)
                    new_state_list[block - 1] = 0

                    new_state_obj = BlocksState(new_state_list)
                    moves.append(((block, 0), new_state_obj))

                # Jeśli klocek leży na stole, można go przełożyć na dowolny wolny klocek.
                if support == 0:
                    for target in free_blocks:
                        if target != block:
                            new_state_list = list(self.state)
                            new_state_list[block - 1] = target

                            new_state_obj = BlocksState(new_state_list)
                            moves.append(((block, target), new_state_obj))

        return moves


    def __eq__(self, other):
        if not isinstance(other, BlocksState):
            return False
        return self.state == other.state


    def __hash__(self):
        return hash(self.state)
