from collections import Counter

# Funkcja wczytująca stan początkowy i docelowy z pliku. Jako argument (filepath) przyjmuje ścieżkę do pliku
# zawierającego opis stanów. Zwraca zmienne start_state oraz target_state będące tablicami z liczbami
# reprezentującymi stany.
def parse_block_file(filepath):
    states = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            state = [int(x) for x in line.split()]
            states.append(state)

            if len(states) == 2:
                break

    if len(states) != 2:
        raise ValueError("Plik nie zawiera dwóch poprawnych układów (startowy i docelowy).")

    start_state = states[0]
    target_state = states[1]

    return start_state, target_state

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
        supported_blocks = set(self.state)
        return [i for i in range(1, self.n + 1) if i not in supported_blocks]


    # Metoda zwracająca tablicę wszystkich możliwych ruchów na układzie.
    def get_possible_moves(self):
        moves = []
        free_blocks = self.get_free_blocks()

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
                    new_state_list = list(self.state)
                    new_state_list[block - 1] = target

                    new_state_obj = BlocksState(new_state_list)
                    moves.append(((block, target), new_state_obj))

        return moves