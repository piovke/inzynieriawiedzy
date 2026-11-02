import json
import re
import sys


def fail(msg: str, path: str = None, line: int = None):
    """Wypisuje komunikat błędu i kończy działanie programu."""
    loc = f" w linii {line}" if line else (f" w {path}" if path else "")
    print(f"Błąd{loc}: {msg}")
    sys.exit(1)


def normalize_name(name: str) -> str:
    """Normalizuje nazwy pakietów, np. Foo_Bar -> foo-bar."""
    return re.sub(r"[-_.]+", "-", name).lower()


def normalize_version(ver: str) -> tuple:
    """Sprowadza wersję do krotki, ignorując końcowe zera, np. 1.0.0 -> (1, 0)."""
    parts = [int(p) for p in ver.split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


class Requirement:
    """Parsuje pojedyncze wymaganie lub konflikt z uwzględnieniem alternatyw '|'."""
    def __init__(self, text: str, current_pkg: str, path: str):
        self.raw_text = text
        self.parsed = []

        # Rozdziela tekst na części oddzielone znakiem alternatywy | a następnie iteruje po nich
        for alt in text.split("|"):
            tokens = alt.strip().split()
            if not tokens:
                fail("Puste wymaganie", path)

            target = normalize_name(tokens[0])
            if target == current_pkg:
                fail("Pakiet nie może wymagać ani konfliktować z samym sobą", path)

            ops = re.findall(r"(==|!=|<=|>=|<|>)\s*(\d+(?:\.\d+)*)", " ".join(tokens[1:]))
            constraints = [(op, normalize_version(v)) for op, v in ops]
            self.parsed.append((target, constraints))


class Repository:
    """Wczytuje i przechowuje bazę wiedzy o repozytorium."""
    def __init__(self, filepath: str):
        self.packages = {}
        self._load(filepath)

    def _load(self, filepath: str):
        def check_dups(pairs):
            keys = set()
            for k, v in pairs:
                if k in keys:
                    fail(f"Powtórzony klucz JSON '{k}'")
                keys.add(k)
            return dict(pairs)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.loads(f.read(), object_pairs_hook=check_dups)
        except json.JSONDecodeError as e:
            fail(e.msg, line=e.lineno)
        except ValueError as e:
            fail(str(e))

        if "packages" not in data:
            fail("Brak pola 'packages'", "$")


        # Iteracja po każdym pakiecie w pliku, sprawdzenie czy po normalizacji nie ma duplikatów
        # oraz czy każdy pakiet ma wymagane pola (versions)
        for pkg_name, pkg_data in data["packages"].items():
            pkg_key = normalize_name(pkg_name)
            pkg_path = f"packages['{pkg_name}']"

            if pkg_key in self.packages:
                fail(f"Duplikat pakietu '{pkg_name}'", pkg_path)

            self.packages[pkg_key] = {}

            if "versions" not in pkg_data:
                fail("Brak pola 'versions'", f"{pkg_path}.versions")

            # Iteruje przez wszystkie wpisane wersje pakietu, normalizuje i sprawdza czy nie ma duplikatów. Następnie
            # tworzy listy obiektów wymagań/konfliktów. Na końcu zapisuje w słowniku
            for ver_str, ver_data in pkg_data["versions"].items():
                ver_key = normalize_version(ver_str)
                path = f"{pkg_path}.versions['{ver_str}']"

                if ver_key in self.packages[pkg_key]:
                    fail(f"Duplikat wersji '{ver_str}'", path)

                reqs = [
                    Requirement(r, pkg_key, f"{path}.requires[{i}]")
                    for i, r in enumerate(ver_data.get("requires", []))
                ]
                confs = [
                    Requirement(c, pkg_key, f"{path}.conflicts[{i}]")
                    for i, c in enumerate(ver_data.get("conflicts", []))
                ]

                self.packages[pkg_key][ver_key] = {
                    "raw_version": ver_str,
                    "requires": reqs,
                    "conflicts": confs
                }


class State:
    """Przechowuje zainstalowany stan środowiska."""
    def __init__(self):
        self.installed = {}

    def install(self, name: str, version: str, manual: bool = False):
        self.installed[normalize_name(name)] = (version, normalize_version(version), manual)

    def remove(self, name: str):
        self.installed.pop(normalize_name(name), None)


import z3
import operator



def version_matches(ver_tuple: tuple, op: str, target_tuple: tuple) -> bool:
    """Porównuje dwie krotki wersji za pomocą odpowiedniego operatora."""
    ops = {
        "==": operator.eq,
        "!=": operator.ne,
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
    }
    return ops[op](ver_tuple, target_tuple)


def get_matching_versions(repo, target_pkg: str, constraints: list) -> list:
    """Zwraca listę kluczy (pakiet, krotka_wersji) spełniających wszystkie ograniczenia."""
    if target_pkg not in repo.packages:
        return []

    matches = []
    for ver_tuple in repo.packages[target_pkg].keys():
        # Wszystkie ograniczenia muszą być spełnione jednocześnie
        if all(version_matches(ver_tuple, op, tgt) for op, tgt in constraints):
            matches.append((target_pkg, ver_tuple))
    return matches


class KnowledgeBase:
    """Baza wiedzy kodująca repozytorium w logice zdań dla solvera Z3."""

    def __init__(self, repo):
        self.repo = repo
        self.x = {}  # Słownik zmiennych: np. {("lib", (1, 0)): z3.Bool("lib==1.0")}

        self.solver = z3.Solver()
        self.solver.set("core.minimize", True)

        self._create_variables()
        self._build_axioms()

    def _create_variables(self):
        """Tworzy zmienną bool (p==v) dla każdej dostępnej wersji w repozytorium."""
        for pkg_name, pkg_data in self.repo.packages.items():
            for ver_tuple, ver_data in pkg_data.items():
                raw_v = ver_data["raw_version"]
                self.x[(pkg_name, ver_tuple)] = z3.Bool(f"{pkg_name}=={raw_v}")

    def _add_axiom(self, formula, label: str):
        """Dodaje sformułowaną regułę przypisując jej etykietę logiczną."""
        self.solver.assert_and_track(formula, z3.Bool(label))

    def _build_axioms(self):
        """Buduje i dodaje trzy wymagane typy aksjomatów."""
        for pkg_name, pkg_data in self.repo.packages.items():

            # (A1) W środowisku może być zainstalowana co najwyżej jedna wersja pakietu
            ver_vars = [self.x[(pkg_name, v)] for v in pkg_data.keys()]
            if ver_vars:
                self._add_axiom(
                    z3.AtMost(*ver_vars, 1),
                    f"A1: {pkg_name} ma co najwyzej jedna wersje"
                )

            for ver_tuple, ver_data in pkg_data.items():
                raw_v = ver_data["raw_version"]
                p_v_var = self.x[(pkg_name, ver_tuple)]

                # (A2) Zależności: zainstalowanie p==v pociąga za sobą jego wymagania
                for req in ver_data["requires"]:
                    alt_vars = []
                    # Zbieranie zmiennych pasujących do alternatyw (operator |)
                    for alt_pkg, constraints in req.parsed:
                        matches = get_matching_versions(self.repo, alt_pkg, constraints)
                        alt_vars.extend([self.x[m] for m in matches])

                    # Jeśli nie ma odpowiednika w repozytorium
                    if not alt_vars:
                        print(f"Ostrzeżenie: Wymaganie '{req.raw_text}' dla {pkg_name}=={raw_v} "
                              "nie pasuje do żadnej wersji w repozytorium.")

                    self._add_axiom(
                        z3.Implies(p_v_var, z3.Or(*alt_vars)),
                        f"A2: {pkg_name}=={raw_v} wymaga {req.raw_text}"
                    )

                # (A3) Konflikty: p==v wyklucza każdą pasującą wersję wskazanego pakietu
                for conf in ver_data["conflicts"]:
                    for alt_pkg, constraints in conf.parsed:
                        matches = get_matching_versions(self.repo, alt_pkg, constraints)
                        conf_vars = [self.x[m] for m in matches]

                        if conf_vars:
                            self._add_axiom(
                                z3.Implies(p_v_var, z3.Not(z3.Or(*conf_vars))),
                                f"A3: {pkg_name}=={raw_v} konfliktuje z {conf.raw_text}"
                            )

    def print_formulas_for_report(self):
        """Wypisuje formuły logiczne w formacie tekstowym."""
        for assertion in self.solver.assertions():
            print(assertion)