import json
import re


# 1. JEDNA KLASA BŁĘDU ZAMIAST SKOMLIKOWANYCH WYJĄTKÓW
class RepositoryError(Exception):
    """Zgłasza błąd z podaniem linii lub ścieżki w pliku[cite: 3]."""

    def __init__(self, msg, path=None, line=None):
        loc = f" w linii {line}" if line else (f" w {path}" if path else "")
        super().__init__(f"Błąd{loc}: {msg}")


# 2. KRÓTKE FUNKCJE POMOCNICZE (BEZ MIESZANIA ICH W GŁÓWNYM KODZIE)
def normalize_name(name: str) -> str:
    """Zamienia 'Foo_Bar' na 'foo-bar'[cite: 2]."""
    return re.sub(r"[-_.]+", "-", name).lower()


def normalize_version(ver: str) -> tuple:
    """Zamienia '1.0.0' na krotkę (1, 0) do łatwego porównywania[cite: 2]."""
    parts = [int(p) for p in ver.split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


# 3. TRZY GŁÓWNE KLASY (WYMAGANIA, REPOZYTORIUM, STAN)
class Requirement:
    """Parsuje pojedyncze wymaganie lub konflikt[cite: 1, 2]."""

    def __init__(self, text: str, current_pkg: str, path: str):
        self.raw_text = text
        self.parsed = []

        for alt in text.split("|"):
            tokens = alt.strip().split()
            target = normalize_name(tokens[0])
            if target == current_pkg:
                raise RepositoryError("Pakiet nie może wymagać/konfliktować z samym sobą", path)

            # Parsowanie operatorów i wersji (np. >=2.0)[cite: 2]
            ops = re.findall(r"(==|!=|<=|>=|<|>)\s*(\d+(?:\.\d+)*)", " ".join(tokens[1:])) #??
            constraints = [(op, normalize_version(v)) for op, v in ops]
            self.parsed.append((target, constraints))


class Repository:
    """Baza wiedzy o repozytorium[cite: 1, 3]."""

    def __init__(self, filepath: str):
        self.packages = {}  # { 'app': { (2, 0): {'requires': [...], 'conflicts': [...]} } }
        self._load(filepath)

    def _load(self, filepath: str):
        # Wykrywanie powtórzonych kluczy w JSON[cite: 4]
        def check_dups(pairs):
            keys = set()
            for k, v in pairs:
                if k in keys: raise ValueError(f"Powtórzony klucz '{k}'")
                keys.add(k)
            return dict(pairs)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.loads(f.read(), object_pairs_hook=check_dups)
        except json.JSONDecodeError as e:
            raise RepositoryError(e.msg, line=e.lineno)
        except ValueError as e:
            raise RepositoryError(str(e))

        if "packages" not in data:
            raise RepositoryError("Brak pola 'packages'", path="$")

        # Wczytywanie pakietów
        for pkg_name, pkg_data in data["packages"].items():
            pkg_key = normalize_name(pkg_name)
            if pkg_key in self.packages:
                raise RepositoryError(f"Duplikat pakietu '{pkg_name}'", path=f"packages['{pkg_name}']")

            self.packages[pkg_key] = {}

            for ver_str, ver_data in pkg_data.get("versions", {}).items():
                ver_key = normalize_version(ver_str)
                path = f"packages['{pkg_name}'].versions['{ver_str}']"

                if ver_key in self.packages[pkg_key]:
                    raise RepositoryError(f"Duplikat wersji '{ver_str}'", path=path)

                # Parsowanie zalecanych list wymagań i konfliktów[cite: 1]
                reqs = [Requirement(r, pkg_key, f"{path}.requires") for r in ver_data.get("requires", [])]
                confs = [Requirement(c, pkg_key, f"{path}.conflicts") for c in ver_data.get("conflicts", [])]

                self.packages[pkg_key][ver_key] = {"raw_version": ver_str, "requires": reqs, "conflicts": confs}


class State:
    """Zarządza stanem zainstalowanych pakietów[cite: 1, 2]."""

    def __init__(self):
        self.installed = {}  # { 'app': ('2.0', (2,0), is_manual) }

    def install(self, name: str, version: str, manual: bool = False):
        self.installed[normalize_name(name)] = (version, normalize_version(version), manual)

    def remove(self, name: str):
        self.installed.pop(normalize_name(name), None)