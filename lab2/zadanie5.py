import time
from main import Repository, State
from zadanie3 import Installer, Requirement
from verify import verify_state


def run_experiments():
    # Rozmiary repozytoriów zdefiniowane w treści zadania
    N_values = [10, 30, 100, 300, 1000]

    for N in N_values:
        # Ścieżki na podstawie struktury katalogów z obrazka (grupa k21)[cite: 8]
        repo_path = f"k21/repo_{N}.json"
        req_path = f"k21/requests_{N}.txt"

        print(f"\n{'=' * 40}\nEKSPERYMENT DLA N = {N}\n{'=' * 40}")

        # 1. POMIAR CZASU BUDOWY BAZY WIEDZY[cite: 4]
        t_build_start = time.time()

        repo = Repository(repo_path)
        installer = Installer(repo)

        t_build_end = time.time()
        build_time = t_build_end - t_build_start

        # 2. ZBIERANIE STATYSTYK BAZY[cite: 4]
        num_versions = sum(len(pkg_data) for pkg_data in repo.packages.values())
        # Ilość reguł wrzuconych do Z3.Optimize()
        num_axioms = len(installer.opt.assertions())

        # 3. WCZYTYWANIE ŻĄDAŃ[cite: 4]
        requests_list = []
        raw_requests = []
        with open(req_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    requests_list.append(Requirement(line, current_pkg="", path=req_path))
                    raw_requests.append(line)
        request_str = ", ".join(raw_requests)

        # 4. POMIAR CZASU ROZWIĄZANIA PRZEZ Z3[cite: 4]
        t_solve_start = time.time()

        # Uwaga: aby nie zaciemniać wyjścia podczas pomiarów, możesz w zadanie3.py
        # zakomentować printy z wypisywaniem zainstalowanych paczek na ekran.
        installed_packages = installer.install(requests_list)

        t_solve_end = time.time()
        solve_time = t_solve_end - t_solve_start

        # 5. GENEROWANIE WYNIKÓW I WERYFIKACJA[cite: 4]
        if installed_packages is not None:
            num_installed = len(installed_packages)
            total_out_of_date = 0

            # Odtwarzamy stan w celu weryfikacji i policzenia przestarzałości
            current_state = State()

            for pkg_str in installed_packages:
                name, version = pkg_str.split(" ", 1)
                current_state.install(name, version)

                # Zliczanie przestarzałości
                for v_tuple, v_data in repo.packages[name].items():
                    if v_data["raw_version"] == version:
                        total_out_of_date += installer.out_of_date[(name, v_tuple)]
                        break

            result_str = f"Zainstalowano {num_installed} pakietów, przestarzałość: {total_out_of_date}"

            # Weryfikacja bez użycia solvera
            print("--- Logi weryfikacji ---")
            try:
                verify_state(repo, current_state, requests_list)
                verification_result = "POZYTYWNA (brak naruszeń)"
            except Exception as e:
                verification_result = f"NEGATYWNA ({e})"
            print("------------------------")

        else:
            result_str = "Brak rozwiązania"
            verification_result = "N/A"

        # 6. WYPISANIE RAPORTU[cite: 4]
        print(f"[RAPORT] Liczba wersji: {num_versions}")
        print(f"[RAPORT] Liczba aksjomatów: {num_axioms}")
        print(f"[RAPORT] Żądanie: {request_str}")
        print(f"[RAPORT] Wynik: {result_str}")
        print(f"[RAPORT] Czas budowy bazy wiedzy (z plikiem): {build_time:.4f} s")
        print(f"[RAPORT] Czas rozwiązania: {solve_time:.4f} s")
        print(f"[RAPORT] Weryfikacja: {verification_result}")


if __name__ == "__main__":
    run_experiments()