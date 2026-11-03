import operator


def version_matches(ver_tuple: tuple, op: str, target_tuple: tuple) -> bool:
    """Funkcja pomocnicza porównująca dwie wersje (krotki) przy użyciu zadanego operatora."""
    ops = {
        "==": operator.eq,
        "!=": operator.ne,
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
    }
    return ops[op](ver_tuple, target_tuple)


def verify_state(repo, state, requests=None) -> bool:
    """
    Weryfikuje poprawność stanu środowiska bez użycia solvera.
    Wypisuje wszystkie naruszone warunki.
    Zwraca True jeśli stan jest spójny, False w przypadku znalezienia błędów.
    """
    violations = []

    # Pomocnicza funkcja do sprawdzania, czy pojedyncza gałąź alternatywy jest spełniona
    def is_alternative_satisfied(target_pkg, constraints):
        if target_pkg not in state.installed:
            return False

        # Pobieramy zainstalowaną krotkę wersji (indeks 1 z krotki stanu)
        inst_ver_tuple = state.installed[target_pkg][1]

        # Wszystkie ograniczenia nałożone na ten konkretny pakiet muszą być spełnione
        return all(version_matches(inst_ver_tuple, op, tgt) for op, tgt in constraints)

    # Sprawdzenie, czy każda zainstalowana wersja w ogóle istnieje w repozytorium
    for pkg, (raw_ver, ver_tuple, is_manual) in state.installed.items():
        if pkg not in repo.packages:
            violations.append(f"Zainstalowany pakiet '{pkg}' nie istnieje w repozytorium.")
            continue
        if ver_tuple not in repo.packages[pkg]:
            violations.append(f"Zainstalowana wersja '{raw_ver}' pakietu '{pkg}' nie istnieje w repozytorium.")

    # Weryfikacja wymagań i konfliktów dla każdego zainstalowanego pakietu
    for pkg, (raw_ver, ver_tuple, _) in state.installed.items():
        # Zabezpieczenie przed błędem, gdy pakietu nie ma w repozytorium
        if pkg not in repo.packages or ver_tuple not in repo.packages[pkg]:
            continue

        ver_data = repo.packages[pkg][ver_tuple]

        # Sprawdzanie wymagań (A2)
        for req in ver_data["requires"]:
            satisfied = False

            # Iterujemy po alternatywach oddzielonych '|'. Wystarczy, że jedna będzie spełniona.
            for alt_pkg, constraints in req.parsed:
                if is_alternative_satisfied(alt_pkg, constraints):
                    satisfied = True
                    break

            if not satisfied:
                violations.append(f"Niespełnione wymaganie '{req.raw_text}' dla paczki {pkg}=={raw_ver}.")

        # Sprawdzanie konfliktów (A3)
        for conf in ver_data["conflicts"]:
            # Konflikty nie mogą mieć alternatyw, więc iteracja wykona się tylko raz na regułę
            for alt_pkg, constraints in conf.parsed:
                if is_alternative_satisfied(alt_pkg, constraints):
                    conflicting_ver = state.installed[alt_pkg][0]
                    violations.append(
                        f"Konflikt: {pkg}=={raw_ver} wyklucza się z zainstalowanym {alt_pkg}=={conflicting_ver} "
                        f"(naruszona reguła: {conf.raw_text})."
                    )

    # 4. Sprawdzenie podanych żądań (np. z pliku zadania.txt)
    if requests:
        for req in requests:
            satisfied = False
            for alt_pkg, constraints in req.parsed:
                if is_alternative_satisfied(alt_pkg, constraints):
                    satisfied = True
                    break

            if not satisfied:
                violations.append(f"Niespełnione żądanie instalacji od użytkownika: '{req.raw_text}'.")

    # Podsumowanie i wypisanie wyników
    if violations:
        print("Znaleziono następujące naruszenia spójności środowiska:")
        for v in violations:
            print(f" ❌ {v}")
        return False

    print("Stan środowiska jest w 100% spójny.")
    return True