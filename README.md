# Ranking Glicko-2
![Python Version](https://img.shields.io/badge/python-3.x-blue)
![License](https://img.shields.io/badge/license-GPLv3-blue)

Aplikacja do zarządzania rankingami zawodników w systemie **Glicko-2** z interfejsem graficznym (GUI) opartym na bibliotece **Tkinter**. Umożliwia dodawanie zawodników, rozgrywanie meczów, automatyczną aktualizację rankingów, wyświetlanie historii meczów, tworzenie wykresów zmian rankingów oraz eksportowanie danych.

---

## 📖 Spis treści
- [🎥 Demo](#-demo)
- [✨ Funkcje](#-funkcje)
- [📋 Wymagania](#-wymagania)
- [⚙️ Instalacja](#️-instalacja)
- [🚀 Uruchomienie](#-uruchomienie)
- [📚 Instrukcja użytkowania](#-instrukcja-użytkowania)
- [📸 Zrzuty ekranu](#-zrzuty-ekranu)
- [💡 Technologie](#-technologie)
- [🔮 Planowane funkcje](#-planowane-funkcje)
- [👋 Wsparcie](#-wsparcie)
- [📜 Licencja](#-licencja)

---

## 🎥 Demo
(GIF)

---

## ✨ Funkcje
- **Dodawanie zawodników**: Możliwość dodawania nowych zawodników z walidacją nazw.
- **Rozgrywanie meczów**: Obsługa meczów z opcją wyboru wyniku (wygrana, remis).
- **Automatyczna aktualizacja rankingów**: System automatycznie aktualizuje rankingi po każdym meczu.
- **Historia meczów**: Przechowywanie i przegląd historii rozegranych meczów.
- **Wykresy zmian rankingów**: Generowanie wykresów przedstawiających zmiany rankingów zawodników.
- **Eksportowanie danych**: Eksportowanie rankingów do pliku CSV.
- **Sortowanie rankingów**: Możliwość sortowania według różnych kryteriów (np. Rating, Procent wygranych).
- **Walidacja danych**: Lepsza walidacja danych i obsługa błędów.

---

## 📋 Wymagania
- **Python 3.x**
- Biblioteki Python:
  - `glicko2`
  - `matplotlib`

---

## ⚙️ Instalacja

### Sklonuj repozytorium:
```bash
git clone https://github.com/unshleepd/Ranking-Glicko.git
```

### Przejdź do katalogu projektu:
```bash
cd Ranking-Glicko
```

### Zainstaluj wymagane biblioteki:
```bash
pip install -r requirements.txt
```

## 🚀 Uruchomienie

### Uruchom aplikację:
```bash
python glicko.py
```

---

## 📚 Instrukcja użytkowania
### Dodawanie zawodników:
- Wpisz nazwę zawodnika w polu "Dodaj Zawodnika".
- Kliknij przycisk "Dodaj".
Nazwa zawodnika może zawierać litery, cyfry, spacje lub podkreślenia (maks. 20 znaków).

### Rozgrywanie meczów:
- Wybierz dwóch zawodników z list rozwijanych.
- Wybierz wynik meczu.
- Kliknij "Rozegraj Mecz".

### Wyświetlanie rankingów:
- Wybierz kryterium sortowania w sekcji "Sortuj według".
- Kliknij "Pokaż Rankingi".

### Wyświetlanie historii meczów:
- Kliknij przycisk "Pokaż Historię Meczów".

### Generowanie wykresu zmian rankingów:
- Wybierz zawodnika w polu "Zawodnik 1".
- Kliknij "Pokaż Wykres".

### Eksportowanie rankingów:
- Kliknij "Eksportuj Rankingi", aby zapisać dane do pliku rankingi.csv.

---

# 📸 Zrzuty ekranu
### Główny interfejs aplikacji:
![Główny interfejs aplikacji](https://i.imgur.com/a10Xazk.png)

### Wykres zmiany rankingu:
![Wykres zmiany rankingu](https://i.imgur.com/PmOXIwM.png)

### Historia meczów:
![Historia meczów](https://i.imgur.com/1m4Hotx.png)

---

## 💡 Technologie
- Python 3.x
- Tkinter - GUI
- Glicko2 - Algorytm obliczania rankingów
- Matplotlib - Wykresy
- Pickle - Zapisywanie danych
- CSV - Eksport danych

---

## 🔮 Planowane funkcje
- Filtrowanie i sortowanie historii meczów.
- Edycja i usuwanie zawodników oraz meczów.
- Importowanie i eksportowanie danych (JSON, Excel).
- Obsługa wielu języków (i18n).


---

## 👋 Wsparcie
Chetnie przeanalizuje wszelkie sugestie.

---

## 📜 Licencja
Projekt objęty licencją GPL. Szczegóły w pliku LICENSE.
