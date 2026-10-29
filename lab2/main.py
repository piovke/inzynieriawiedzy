import json
import re
import sys


def fail(msg: str, path: str = None, line: int = None):
    """Drukuje komunikat błędu i natychmiast kończy działanie programu[cite: 3]."""
    loc = f" w linii {line}" if line else (f" w {path}" if path else "")
    print(f"Błąd{loc}: {msg}")
    sys.exit(1)


def normalize_name(name: str) -> str:
    """Normalizuje nazwy pakietów, np. Foo_Bar -> foo-bar[cite: 2]."""
    return re.sub(r"[-_.]+", "-", name).lower()


def normalize_version(ver: str) -> tuple:
    """Sprowadza wersję do krotki, ignorując końcowe zera, np. 1.0.0 -> (1, 0)[cite: 2]."""
    parts = [int(p) for p in ver.split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


class Requirement:
    """Parsuje pojedyncze wymaganie lub konflikt z uwzględnieniem alternatyw '|'[cite: 1, 2]."""
    def __init__(self, text: str, current_pkg: str, path: str):
        self.raw_text = text
        self.parsed = []

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
    """Wczytuje i przechowuje bazę wiedzy o repozytorium[cite: 1, 3]."""
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

        for pkg_name, pkg_data in data["packages"].items():
            pkg_key = normalize_name(pkg_name)
            pkg_path = f"packages['{pkg_name}']"

            if pkg_key in self.packages:
                fail(f"Duplikat pakietu '{pkg_name}'", pkg_path)

            self.packages[pkg_key] = {}

            if "versions" not in pkg_data:
                fail("Brak pola 'versions'", f"{pkg_path}.versions")

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
    """Przechowuje zainstalowany stan środowiska[cite: 1, 2]."""
    def __init__(self):
        self.installed = {}

    def install(self, name: str, version: str, manual: bool = False):
        self.installed[normalize_name(name)] = (version, normalize_version(version), manual)

    def remove(self, name: str):
        self.installed.pop(normalize_name(name), None)