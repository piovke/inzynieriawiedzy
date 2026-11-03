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


VERSION_RE = re.compile(r"^\d+(\.\d+)*$")


def normalize_version(ver: str, path: str = None, line: int = None) -> tuple:
    """Sprowadza wersję do krotki, ignorując końcowe zera, np. 1.0.0 -> (1,)."""
    if not VERSION_RE.match(ver):
        fail(f"Niepoprawna wersja '{ver}'", path, line)
    parts = [int(p) for p in ver.split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


NAME_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*(.*)$")
CONSTRAINT_RE = re.compile(r"\s*(==|!=|<=|>=|<|>)\s*(\d+(?:\.\d+)*)\s*(?:,|\s|$)")


def parse_constraints(rest: str):
    """Zwraca listę (op, krotka_wersji) albo None, jeśli reszta tekstu jest niepoprawna."""
    rest = rest.strip()
    constraints, pos = [], 0
    while pos < len(rest):
        m = CONSTRAINT_RE.match(rest, pos)
        if not m:
            return None
        constraints.append((m.group(1), normalize_version(m.group(2))))
        pos = m.end()
    return constraints


class Requirement:
    """Parsuje pojedyncze wymaganie lub konflikt z uwzględnieniem alternatyw '|'."""

    def __init__(self, text: str, current_pkg: str, path: str, line: int = None, allow_alt: bool = True):
        self.raw_text = text
        self.parsed = []

        if not allow_alt and "|" in text:
            fail("Konflikt nie może zawierać alternatywy '|'", path, line)

        for alt in text.split("|"):
            m = NAME_RE.match(alt)
            if not m:
                fail("Puste lub niepoprawne wymaganie", path, line)

            target = normalize_name(m.group(1))
            constraints = parse_constraints(m.group(2))
            if constraints is None:
                fail(f"Niepoprawne ograniczenie wersji w '{alt.strip()}'", path, line)
            if target == current_pkg:
                fail("Pakiet nie może wymagać ani konfliktować z samym sobą", path, line)

            self.parsed.append((target, constraints))


NAME_VALID_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


class Repository:
    """Wczytuje, waliduje i przechowuje bazę wiedzy o repozytorium."""
    def __init__(self, filepath: str):
        self.packages = {}
        self._load(filepath)
        self._warn_unmatched()

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
        except OSError as e:
            fail(f"Nie można otworzyć pliku: {e}")
        except json.JSONDecodeError as e:
            fail(e.msg, line=e.lineno)
        except ValueError as e:
            fail(str(e))

        # --- korzeń dokumentu ---
        if not isinstance(data, dict):
            fail("Korzeń dokumentu musi być obiektem", "$")
        for key in data:
            if key not in ("meta", "packages"):
                fail(f"Nieznane pole '{key}'", "$")
        if "packages" not in data:
            fail("Brak pola 'packages'", "$")
        if not isinstance(data["packages"], dict):
            fail("Pole 'packages' musi być obiektem", "packages")

        # --- pakiety ---
        for pkg_name, pkg_data in data["packages"].items():
            pkg_path = f"packages['{pkg_name}']"

            if not NAME_VALID_RE.match(pkg_name):
                fail(f"Niepoprawna nazwa pakietu '{pkg_name}'", pkg_path)
            pkg_key = normalize_name(pkg_name)
            if pkg_key in self.packages:
                fail(f"Duplikat pakietu '{pkg_name}'", pkg_path)

            if not isinstance(pkg_data, dict):
                fail("Pakiet musi być obiektem", pkg_path)
            for key in pkg_data:
                if key != "versions":
                    fail(f"Nieznane pole '{key}'", pkg_path)
            if "versions" not in pkg_data:
                fail("Brak pola 'versions'", f"{pkg_path}.versions")
            if not isinstance(pkg_data["versions"], dict):
                fail("Pole 'versions' musi być obiektem", f"{pkg_path}.versions")

            self.packages[pkg_key] = {}

            # --- wersje ---
            for ver_str, ver_data in pkg_data["versions"].items():
                path = f"{pkg_path}.versions['{ver_str}']"
                ver_key = normalize_version(ver_str, path)

                if ver_key in self.packages[pkg_key]:
                    fail(f"Duplikat wersji '{ver_str}'", path)

                if not isinstance(ver_data, dict):
                    fail("Wersja musi być obiektem", path)
                for key in ver_data:
                    if key not in ("requires", "conflicts"):
                        fail(f"Nieznane pole '{key}'", path)

                lists = {}
                for field in ("requires", "conflicts"):
                    items = ver_data.get(field, [])
                    if not isinstance(items, list):
                        fail(f"Pole '{field}' musi być listą napisów", f"{path}.{field}")
                    for i, item in enumerate(items):
                        if not isinstance(item, str):
                            fail("Element musi być napisem", f"{path}.{field}[{i}]")
                    lists[field] = items

                reqs = [
                    Requirement(r, pkg_key, f"{path}.requires[{i}]")
                    for i, r in enumerate(lists["requires"])
                ]
                confs = [
                    Requirement(c, pkg_key, f"{path}.conflicts[{i}]", allow_alt=False)
                    for i, c in enumerate(lists["conflicts"])
                ]

                self.packages[pkg_key][ver_key] = {
                    "raw_version": ver_str,
                    "requires": reqs,
                    "conflicts": confs
                }

    def _warn_unmatched(self):
        """Ostrzega o wymaganiach i konfliktach, którym nie odpowiada żadna wersja w repo."""
        for pkg, versions in self.packages.items():
            for ver_data in versions.values():
                raw_v = ver_data["raw_version"]
                for req in ver_data["requires"]:
                    if not any(get_matching_versions(self, p, c) for p, c in req.parsed):
                        print(f"Ostrzeżenie: Wymaganie '{req.raw_text}' dla {pkg}=={raw_v} "
                              "nie pasuje do żadnej wersji w repozytorium.")
                for conf in ver_data["conflicts"]:
                    if not any(get_matching_versions(self, p, c) for p, c in conf.parsed):
                        print(f"Ostrzeżenie: Konflikt '{conf.raw_text}' dla {pkg}=={raw_v} "
                              "nie pasuje do żadnej wersji w repozytorium.")

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