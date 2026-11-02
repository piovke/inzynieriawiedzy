to szczegółowa mapa architektury Twojego projektu. Cały system działa jak fabryka (pipeline), w której surowe pliki tekstowe są przetwarzane na obiekty, z obiektów budowane są równania matematyczne, a na końcu matematyka jest z powrotem tłumaczona na listę pakietów.

Poniżej znajduje się podział na główne bloki i opis, jak ze sobą współpracują.

### **1\. Warstwa Danych Wejściowych (Pliki)**

To tutaj projekt kontaktuje się ze światem zewnętrznym.

* **Repozytorium (np. repo\_10.json)**: Plik JSON zawierający definicje pakietów, ich wersji, zależności (requires) i konfliktów (conflicts).  
* **Plik żądań (np. requests\_10.txt)**: Lista paczek (i ewentualnie ich konkretnych wersji), które użytkownik chce zainstalować (np. app \==2.0, tool).  
* *(Opcjonalnie dla wyższych ocen)* **Plik stanu (np. state.txt)**: Plik przechowujący informację o tym, co już jest na komputerze zainstalowane.

### **2\. Warstwa Modelu Domenowego (Parsery)**

Te klasy tłumaczą surowe pliki na "język" zrozumiały dla Pythona.

* **Klasa Requirement**: To Twój uniwersalny tłumacz. Wchodzi do niej surowy tekst (np. lib \>=2.0 \<3.0 \| util), a wychodzi ustrukturyzowana lista alternatyw, pakietów, operatorów logicznych i wyłuskanych krotek wersji (np. (2, 0\)). Używana jest zarówno do parsowania plików JSON (wymagania pakietów), jak i plików TXT (żądania użytkownika).  
* **Klasa Repository**: To wewnętrzna baza danych. Otwiera plik JSON, waliduje jego strukturę, wykrywa duplikaty i tworzy wielki słownik. Słownik ten dla każdej udostępnianej wersji przechowuje obiekty Requirement jako listy jej zależności i konfliktów.  
* **Klasa State**: Reprezentuje "migawkę" systemu. Zapisuje, które pakiety i w jakich wersjach są aktualnie wybrane jako zainstalowane, oraz czy zainstalowano je ręcznie, czy z automatu.

### **3\. Warstwa Solvera (Logika Z3)**

To "mózg" całego projektu, operujący wyłącznie na zmiennych logicznych (prawda/fałsz).

* **Klasa KnowledgeBase (Zadanie 2\)**:  
  * **Co wchodzi:** Obiekt Repository.  
  * **Co robi:** Dla każdej wersji pakietu w Repository tworzy zmienną Z3, np. z3.Bool("lib==1.0"). Następnie buduje "twarde" zasady fizyki środowiska: (A1) może być tylko jedna wersja pakietu, (A2) zmienna włączona wymusza włączenie jej zależności (przez z3.Implies), (A3) wyklucza konflikty.  
* **Klasa Installer (Zadanie 3\)**:  
  * **Co wchodzi:** Obiekt Repository oraz lista żądań użytkownika w formie obiektów Requirement.  
  * **Co robi:** Dziedziczy/kopiuje zasady z KnowledgeBase, ale używa z3.Optimize(). Zmusza solver, aby żądania użytkownika miały wartość True. Następnie nakłada "miękkie" cele (kryteria leksykograficzne): minimalizację przestarzałości czy minimalizację liczby instalowanych pakietów (przez użycie z3.Sum i z3.If).  
  * **Co wychodzi:** Jeśli opt.check() \== z3.sat, zwraca nową listę zainstalowanych pakietów.

### **4\. Warstwa Weryfikacji (Zadanie 4\)**

* **Funkcja verify\_state**:  
  * To niezależny "sędzia". Nie ma pojęcia, jak Z3 doszło do swojego wyniku.  
  * **Co wchodzi:** Oryginalne Repository, lista żądań użytkownika i wygenerowany przez solver wynik w formie obiektu State.  
  * **Co robi:** Sprawdza to samo, ale czystym kodem Pythona. Przegląda pakiet po pakiecie w obiekcie State i weryfikuje, czy istnieje on w Repository, czy ma spełnione wymagania i czy z niczym nie konfliktuje.

### **Krok po kroku: Jak przepływają dane? (Scenariusz głównego skryptu)**

Wyobraź sobie uruchomienie skryptu (np. zadanie5.py):

1. **START:** Podajesz ścieżki do repo\_10.json i requests\_10.txt.  
2. **PARSOWANIE REPO:** Tworzysz obiekt repo \= Repository("repo\_10.json"). Klasa otwiera plik, czyta go i dla każdego wymogu tworzy w tle obiekty Requirement.  
3. **PARSOWANIE ŻĄDAŃ:** Otwierasz plik requests\_10.txt, czytasz linijka po linijce i tworzysz dla każdej linijki nowy obiekt Requirement.  
4. **Z3 OPTYMALIZATOR:** Tworzysz installer \= Installer(repo). Installer wczytuje słownik z repo, spłaszcza go do zmiennych logicznych i ustawia ograniczenia (AtMost 1, Implies).  
5. **ROZWIĄZANIE:** Wołasz installer.install(lista\_żądań). Z3 oblicza najlepszą kombinację (uwzględniając przestarzałość, którą obliczyłeś przy inicjalizacji) i oddaje listę stringów, np. \["app 2.0", "lib 2.0", "util 2.0"\].  
6. **BUDOWA STANU:** Kod główny bierze tę listę i wpycha ją do pustego obiektu State, zamieniając to na "oficjalny" stan środowiska.  
7. **WERYFIKACJA:** Obiekt State leci do funkcji verify\_state, która upewnia się, że Z3 nie oszukało i wynik jest spójny.  
8. **KONIEC:** Drukowany jest raport z wynikami, czasem trwania i statystykami.

