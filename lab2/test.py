from main import Repository, KnowledgeBase
from zadanie3 import Installer, Requirement
from verify import *

# Inicjalizujemy klasy z Zadania 1 i 2
repo = Repository("k21/repo_10.json")
kb = KnowledgeBase(repo)

# Zbieramy surowe formuły Z3 prosto do raportu
kb.print_formulas_for_report()


# Parsowanie surowego pliku do obiektów Requirement
parsed_requests = []
with open("k21/requests_10.txt", "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # current_pkg="" bo zapytania usera nie pochodzą z żadnego pakietu
        parsed_requests.append(Requirement(line, current_pkg="", path="k21/requests_10.txt"))

installer = Installer(repo)
installed_packages = installer.install(parsed_requests)

# ==============================================================================
# UŻYCIE WERYFIKACJI (ZADANIE 4)
# ==============================================================================

# Jeśli solver znalazł rozwiązanie (nie zwrócił None)
if installed_packages is not None:
    # 1. Tworzymy obiekt State dla sprawdzanego środowiska[cite: 1]
    current_state = State()

    # 2. Wypełniamy stan wynikami zwróconymi przez instalatora[cite: 4]
    for pkg_str in installed_packages:
        # Zakładamy, że installer zwraca listę stringów w formacie "nazwa wersja", np. "app 2.0"
        name, version = pkg_str.split(" ", 1)
        current_state.install(name, version)

    # 3. Uruchamiamy procedurę weryfikującą[cite: 4]
    print("\n--- Rozpoczęcie weryfikacji (Zadanie 4) ---")
    verify_state(repo, current_state, parsed_requests)
    print("--- Zakończenie weryfikacji ---")
else:
    print("\nBrak rozwiązania z solvera, pomijam weryfikację.")