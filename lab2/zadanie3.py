import z3
from main import *

class Installer:
    """Odpowiada za znalezienie optymalnego środowiska spełniającego żądania[cite: 4]."""

    def __init__(self, repo):
        self.repo = repo
        self.opt = z3.Optimize()
        self.opt.set(priority="lex")  # Optymalizacja leksykograficzna[cite: 6]

        self.x = {}
        self.out_of_date = {}  # Przechowuje indeks przestarzałości dla (pakiet, krotka_wersji)

        self._init_variables()
        self._add_axioms()

    def _init_variables(self):
        """Tworzy zmienne logiczne i wylicza przestarzałość wersji[cite: 1, 6]."""
        for pkg, pkg_data in self.repo.packages.items():
            # Sortowanie malejąco wg krotek daje najnowszą wersję na indeksie 0[cite: 1]
            sorted_vers = sorted(pkg_data.keys(), reverse=True)
            for idx, ver_tuple in enumerate(sorted_vers):
                raw_v = pkg_data[ver_tuple]["raw_version"]
                self.x[(pkg, ver_tuple)] = z3.Bool(f"{pkg}=={raw_v}")
                self.out_of_date[(pkg, ver_tuple)] = idx

    def _add_axioms(self):
        """Kopiuje zasady A1, A2, A3 z bazy wiedzy do optymalizatora[cite: 4, 6]."""
        for pkg, pkg_data in self.repo.packages.items():
            # (A1) Maksymalnie jedna wersja pakietu[cite: 4, 6]
            vars_p = [self.x[(pkg, v)] for v in pkg_data.keys()]
            if vars_p:
                self.opt.add(z3.AtMost(*vars_p, 1))

            for ver, ver_data in pkg_data.items():
                var_pv = self.x[(pkg, ver)]

                # (A2) Zależności[cite: 4, 6]
                for req in ver_data["requires"]:
                    alt_vars = []
                    for alt_pkg, constraints in req.parsed:
                        matches = get_matching_versions(self.repo, alt_pkg, constraints)
                        alt_vars.extend([self.x[m] for m in matches])
                    self.opt.add(z3.Implies(var_pv, z3.Or(*alt_vars)))

                # (A3) Konflikty[cite: 4, 6]
                for conf in ver_data["conflicts"]:
                    for alt_pkg, constraints in conf.parsed:
                        matches = get_matching_versions(self.repo, alt_pkg, constraints)
                        if matches:
                            conf_vars = [self.x[m] for m in matches]
                            self.opt.add(z3.Implies(var_pv, z3.Not(z3.Or(*conf_vars))))

    def install(self, requests_list):
        """Znajduje rozwiązanie dla żądań R do pustego środowiska[cite: 4]."""
        requested_packages = set()

        # 1. WYMUSZENIE INSTALACJI ŻĄDANYCH PAKIETÓW
        for req in requests_list:
            req_vars = []
            for alt_pkg, constraints in req.parsed:
                requested_packages.add(alt_pkg)  # Zapamiętujemy, o jakie pakiety prosił user
                matches = get_matching_versions(self.repo, alt_pkg, constraints)
                req_vars.extend([self.x[m] for m in matches])

            if not req_vars:
                print(f"Błąd: Żądanie '{req.raw_text}' nie odpowiada żadnej wersji w repo.")
                return None

            # Wymagamy, aby przynajmniej jedna zmienna pasująca do żądania była prawdą[cite: 6]
            self.opt.add(z3.Or(*req_vars))

        # 2. DEFINIOWANIE KRYTERIÓW OPTYMALIZACJI (LEKSYKOGRAFICZNIE)[cite: 4]

        # Kryterium 1: minimalna przestarzałość pakietów żądanych[cite: 4]
        c1_terms = []
        for pkg in requested_packages:
            if pkg in self.repo.packages:
                for ver in self.repo.packages[pkg].keys():
                    c1_terms.append(z3.If(self.x[(pkg, ver)], self.out_of_date[(pkg, ver)], 0))
        self.opt.minimize(z3.Sum(c1_terms) if c1_terms else 0)

        # Kryterium 2: minimalna liczba zainstalowanych pakietów[cite: 4, 7]
        c2_terms = [z3.If(var, 1, 0) for var in self.x.values()]
        self.opt.minimize(z3.Sum(c2_terms) if c2_terms else 0)

        # Kryterium 3: minimalna przestarzałość pozostałych pakietów[cite: 4]
        c3_terms = []
        for (pkg, ver), var in self.x.items():
            if pkg not in requested_packages:
                c3_terms.append(z3.If(var, self.out_of_date[(pkg, ver)], 0))
        self.opt.minimize(z3.Sum(c3_terms) if c3_terms else 0)

        # 3. ROZWIĄZANIE I ZWRÓCENIE WYNIKU
        if self.opt.check() == z3.sat:
            m = self.opt.model()
            installed = []
            for (pkg, ver), var in self.x.items():
                if z3.is_true(m.eval(var)):
                    installed.append(f"{pkg} {self.repo.packages[pkg][ver]['raw_version']}")

            print("Zainstalowano paczki:")
            for p in installed:
                print(f" + {p}")
            return installed
        else:
            # Komunikat o braku rozwiązania zgodnie z wymogiem[cite: 4]
            print("Brak rozwiązania")
            return None