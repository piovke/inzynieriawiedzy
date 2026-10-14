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