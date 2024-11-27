# glicko.py
# -*- coding: utf-8 -*-

"""
Aplikacja do zarządzania rankingami zawodników w systemie Glicko-2 z interfejsem
graficznym (GUI) opartym na bibliotece Tkinter. Umożliwia dodawanie zawodników,
rozgrywanie meczów, automatyczną aktualizację rankingów, wyświetlanie historii meczów,
tworzenie wykresów zmian rankingów oraz wyświetlanie łącznej klasyfikacji.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import pickle
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from glicko2 import Player  # Upewnij się, że masz zainstalowany moduł glicko2
from tkinter import filedialog
import os  # Dodano do obsługi plików


class Zawodnik:
    """
    Klasa reprezentująca zawodnika w systemie rankingowym Glicko-2.
    """

    def __init__(self, nazwa, rating=None, rd=None, vol=None):
        self.nazwa = nazwa
        self.player = Player()
        if rating is not None:
            self.player.rating = rating
        if rd is not None:
            self.player.rd = rd
        if vol is not None:
            self.player.vol = vol
        self.oponenci = []
        self.wygrane = 0
        self.przegrane = 0
        self.remisy = 0
        self.historia_ratingow = [self.player.rating]
        self.historia_meczow = []

    def dodaj_mecz(self, przeciwnik, wynik):
        self.oponenci.append((przeciwnik.player, wynik))
        self.historia_meczow.append((przeciwnik.nazwa, wynik))

    def get_state(self):
        state = {
            "nazwa": self.nazwa,
            "rating": self.player.rating,
            "rd": self.player.rd,
            "vol": self.player.vol,
            "wygrane": self.wygrane,
            "przegrane": self.przegrane,
            "remisy": self.remisy,
            "historia_ratingow": self.historia_ratingow,
            "historia_meczow": self.historia_meczow,
        }
        return state

    @classmethod
    def from_state(cls, state):
        zawodnik = cls(
            nazwa=state["nazwa"],
            rating=state["rating"],
            rd=state["rd"],
            vol=state["vol"],
        )
        zawodnik.wygrane = state.get("wygrane", 0)
        zawodnik.przegrane = state.get("przegrane", 0)
        zawodnik.remisy = state.get("remisy", 0)
        zawodnik.historia_ratingow = state.get(
            "historia_ratingow", [state["rating"]]
        )
        zawodnik.historia_meczow = state.get("historia_meczow", [])
        return zawodnik


class Aplikacja:
    """
    Klasa reprezentująca główną aplikację GUI do zarządzania rankingami zawodników.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Ranking Glicko-2")

        self.zawodnicy = {}
        self.historia_meczow = []

        # Ustawienie motywu na "clam"
        style = ttk.Style()
        style.theme_use("clam")

        # Dodanie obsługi zamykania aplikacji
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Automatyczne wczytanie danych
        self.automatic_load_data()

        self.tworz_widgets()

        # Teraz możemy bezpiecznie wywołać odświeżenie list zawodników
        self.odswiez_listy_zawodnikow()
        self.pokaz_klasyfikacje()

    def automatic_load_data(self):
        # Automatyczne wczytywanie danych z pliku 'dane.pkl' przy starcie aplikacji
        filepath = "dane.pkl"
        if os.path.exists(filepath):
            try:
                with open(filepath, "rb") as f:
                    data = pickle.load(f)
                self.zawodnicy = {
                    nazwa: Zawodnik.from_state(state)
                    for nazwa, state in data.get("zawodnicy", {}).items()
                }
                self.historia_meczow = data.get("historia_meczow", [])
                # Przelicz rankingi na podstawie wczytanej historii meczów
                self.przelicz_rankingi()
                print("Dane zostały automatycznie wczytane.")
            except Exception as e:
                messagebox.showerror(
                    "Błąd", f"Błąd podczas automatycznego wczytywania danych: {e}"
                )

    def on_closing(self):
        # Funkcja wywoływana przy zamykaniu aplikacji
        self.automatic_save_data()
        self.root.destroy()

    def automatic_save_data(self):
        # Automatyczne zapisywanie danych do pliku 'dane.pkl' przy zamykaniu aplikacji
        filepath = "dane.pkl"
        try:
            data = {
                "zawodnicy": {
                    nazwa: zawodnik.get_state()
                    for nazwa, zawodnik in self.zawodnicy.items()
                },
                "historia_meczow": self.historia_meczow,
            }
            with open(filepath, "wb") as f:
                pickle.dump(data, f)
            print("Dane zostały automatycznie zapisane.")
        except Exception as e:
            messagebox.showerror(
                "Błąd", f"Błąd podczas automatycznego zapisywania danych: {e}"
            )

    def tworz_widgets(self):
        # Tworzenie menu
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Menu "Plik"
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Plik", menu=file_menu)
        file_menu.add_command(label="Zapisz", command=self.zapisz_dane)
        file_menu.add_command(label="Wczytaj", command=self.wczytaj_dane)
        file_menu.add_separator()
        file_menu.add_command(
            label="Eksportuj Rankingi", command=self.eksportuj_rankingi
        )
        file_menu.add_command(label="Importuj Mecze", command=self.importuj_mecze)
        file_menu.add_command(label="Eksportuj Mecze", command=self.eksportuj_mecze)
        file_menu.add_separator()
        file_menu.add_command(label="Wyjście", command=self.on_closing)

        # Tworzenie notebooka (zakładek)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tworzenie wszystkich zakładek
        self.tab_zawodnicy = ttk.Frame(self.notebook)
        self.tab_rozgrywki = ttk.Frame(self.notebook)
        self.tab_klasyfikacja = ttk.Frame(self.notebook)

        # Dodawanie zakładek do notebooka
        self.notebook.add(self.tab_zawodnicy, text="Zawodnicy")
        self.notebook.add(self.tab_rozgrywki, text="Rozgrywki")
        self.notebook.add(self.tab_klasyfikacja, text="Łączna Klasyfikacja")

        # Tworzenie widżetów w zakładkach
        self.tworz_tab_zawodnicy()
        self.tworz_tab_rozgrywki()
        self.tworz_tab_klasyfikacja()

    def tworz_tab_zawodnicy(self):
        # Implementacja zakładki "Zawodnicy"
        players_frame = ttk.Frame(self.tab_zawodnicy, padding="10")
        players_frame.pack(fill=tk.BOTH, expand=True)

        # Sekcja dodawania zawodników
        add_player_frame = ttk.LabelFrame(
            players_frame, text="Dodaj Zawodnika", padding="10"
        )
        add_player_frame.pack(fill=tk.X, pady=5)

        # Pole tekstowe do wpisywania nazwy zawodnika
        self.entry_player_name = ttk.Entry(add_player_frame)
        self.entry_player_name.grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.E
        )

        # Przycisk "Dodaj" do dodawania zawodnika
        add_button = ttk.Button(
            add_player_frame, text="Dodaj", command=self.dodaj_zawodnika_gui
        )
        add_button.grid(row=0, column=1, padx=5, pady=5)

        add_player_frame.columnconfigure(0, weight=1)

        # Sekcja listy zawodników
        list_frame = ttk.LabelFrame(
            players_frame, text="Lista Zawodników", padding="10"
        )
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Lista zawodników
        self.listbox_players = tk.Listbox(list_frame)
        self.listbox_players.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox_players.bind("<<ListboxSelect>>", self.zaznacz_zawodnika)

        # Dodanie paska przewijania
        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox_players.yview)
        self.listbox_players.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Sekcja akcji na zawodnikach
        action_frame = ttk.Frame(players_frame)
        action_frame.pack(fill=tk.X, pady=5)

        # Przycisk "Usuń Zawodnika"
        delete_button = ttk.Button(
            action_frame, text="Usuń Zawodnika", command=self.usun_zawodnika_gui
        )
        delete_button.pack(side=tk.LEFT, padx=5)

        # Przycisk "Edytuj Zawodnika"
        edit_button = ttk.Button(
            action_frame, text="Edytuj Zawodnika", command=self.edytuj_zawodnika_gui
        )
        edit_button.pack(side=tk.LEFT, padx=5)

        # Przycisk "Importuj Zawodników"
        import_button = ttk.Button(
            action_frame, text="Importuj Zawodników", command=self.importuj_zawodnikow
        )
        import_button.pack(side=tk.LEFT, padx=5)

        # Przycisk "Eksportuj Zawodników"
        export_button = ttk.Button(
            action_frame, text="Eksportuj Zawodników", command=self.eksportuj_zawodnikow
        )
        export_button.pack(side=tk.LEFT, padx=5)

        # Sekcja szczegółów zawodnika
        details_frame = ttk.LabelFrame(
            players_frame, text="Szczegóły Zawodnika", padding="10"
        )
        details_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Wybór zawodnika do wyświetlenia szczegółów
        ttk.Label(details_frame, text="Wybierz Zawodnika:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.var_selected_player = tk.StringVar()
        self.combo_selected_player = ttk.Combobox(
            details_frame, textvariable=self.var_selected_player, state="readonly"
        )
        self.combo_selected_player.grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )
        self.combo_selected_player.bind(
            "<<ComboboxSelected>>", self.odswiez_dane_zawodnika
        )

        # Przycisk "Pokaż Historię Meczów"
        historia_button = ttk.Button(
            details_frame,
            text="Pokaż Historię Meczów",
            command=self.pokaz_historia_meczow_zawodnika,
        )
        historia_button.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        # Przycisk "Pokaż Wykres"
        plot_button = ttk.Button(
            details_frame, text="Pokaż Wykres", command=self.pokaz_wykres_zawodnika
        )
        plot_button.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        details_frame.columnconfigure(1, weight=1)

    def tworz_tab_rozgrywki(self):
        # Implementacja zakładki "Rozgrywki"
        play_match_frame = ttk.LabelFrame(
            self.tab_rozgrywki, text="Rozegraj Mecz", padding="10"
        )
        play_match_frame.pack(fill=tk.X, pady=5, padx=10)

        # Wybór zawodnika 1
        ttk.Label(play_match_frame, text="Zawodnik 1:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.var_player1 = tk.StringVar()
        self.combo_player1 = ttk.Combobox(
            play_match_frame, textvariable=self.var_player1, state="readonly"
        )
        self.combo_player1.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Wybór zawodnika 2
        ttk.Label(play_match_frame, text="Zawodnik 2:").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.var_player2 = tk.StringVar()
        self.combo_player2 = ttk.Combobox(
            play_match_frame, textvariable=self.var_player2, state="readonly"
        )
        self.combo_player2.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Wybór wyniku meczu
        ttk.Label(play_match_frame, text="Wynik:").grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.var_result = tk.StringVar(value="Wygrana Zawodnika 1")

        # Radio buttons dla wyniku
        wynik_frame = ttk.Frame(play_match_frame)
        wynik_frame.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(
            wynik_frame,
            text="Wygrana Zawodnika 1",
            variable=self.var_result,
            value="Wygrana Zawodnika 1",
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            wynik_frame,
            text="Remis",
            variable=self.var_result,
            value="Remis",
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            wynik_frame,
            text="Wygrana Zawodnika 2",
            variable=self.var_result,
            value="Wygrana Zawodnika 2",
        ).pack(anchor=tk.W)

        # Przycisk "Rozegraj Mecz"
        play_button = ttk.Button(
            play_match_frame, text="Rozegraj Mecz", command=self.rozegrac_mecz_gui
        )
        play_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        play_match_frame.columnconfigure(1, weight=1)

    def tworz_tab_klasyfikacja(self):
        # Implementacja zakładki "Łączna Klasyfikacja"
        classification_frame = ttk.Frame(self.tab_klasyfikacja, padding="10")
        classification_frame.pack(fill=tk.BOTH, expand=True)

        # Tworzenie tabeli
        columns = (
            "POZYCJA",
            "IMIĘ",
            "RANKING",
            "%WYGRANYCH",
            "LICZBA PUNKTÓW/GIER",
            "LICZBA PUNKTÓW",
            "LICZBA GIER",
            "WYGRANE",
            "REMISY",
            "PRZEGRANE",
        )
        self.tree = ttk.Treeview(
            classification_frame, columns=columns, show="headings"
        )
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=100)
        self.tree.column("POZYCJA", width=70)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Dodanie paska przewijania
        scrollbar = ttk.Scrollbar(
            classification_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def odswiez_listy_zawodnikow(self):
        # Odświeżenie listy w zakładce Zawodnicy
        self.listbox_players.delete(0, tk.END)
        for nazwa in sorted(self.zawodnicy.keys()):
            self.listbox_players.insert(tk.END, nazwa)

        # Odświeżenie comboboxów w zakładce Rozgrywki
        zawodnicy_list = sorted(self.zawodnicy.keys())
        self.combo_player1['values'] = zawodnicy_list
        self.combo_player2['values'] = zawodnicy_list

        # Odświeżenie comboboxa w zakładce Zawodnicy
        self.combo_selected_player['values'] = zawodnicy_list

    # Metody obsługi zawodników
    def dodaj_zawodnika_gui(self):
        nazwa = self.entry_player_name.get().strip()
        if not nazwa:
            messagebox.showwarning("Błąd", "Nazwa zawodnika nie może być pusta.")
            return
        if nazwa in self.zawodnicy:
            messagebox.showwarning("Błąd", "Zawodnik o tej nazwie już istnieje.")
            return
        self.zawodnicy[nazwa] = Zawodnik(nazwa)
        self.entry_player_name.delete(0, tk.END)
        self.odswiez_listy_zawodnikow()
        self.pokaz_klasyfikacje()
        messagebox.showinfo("Sukces", f"Dodano zawodnika '{nazwa}'.")

    def usun_zawodnika_gui(self):
        selected_indices = self.listbox_players.curselection()
        if selected_indices:
            index = selected_indices[0]
            nazwa = self.listbox_players.get(index)
            if messagebox.askyesno(
                "Potwierdzenie", f"Czy na pewno chcesz usunąć zawodnika '{nazwa}'?"
            ):
                del self.zawodnicy[nazwa]
                self.odswiez_listy_zawodnikow()
                self.pokaz_klasyfikacje()
                messagebox.showinfo("Sukces", f"Usunięto zawodnika '{nazwa}'.")
        else:
            messagebox.showwarning("Błąd", "Nie wybrano zawodnika do usunięcia.")

    def edytuj_zawodnika_gui(self):
        selected_indices = self.listbox_players.curselection()
        if selected_indices:
            index = selected_indices[0]
            nazwa = self.listbox_players.get(index)
            zawodnik = self.zawodnicy[nazwa]

            # Okno dialogowe do edycji zawodnika
            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"Edytuj Zawodnika - {nazwa}")

            ttk.Label(edit_window, text="Nazwa:").grid(row=0, column=0, padx=5, pady=5)
            entry_nazwa = ttk.Entry(edit_window)
            entry_nazwa.insert(0, zawodnik.nazwa)
            entry_nazwa.grid(row=0, column=1, padx=5, pady=5)

            def zapisz_zmiany():
                nowa_nazwa = entry_nazwa.get().strip()
                if not nowa_nazwa:
                    messagebox.showwarning("Błąd", "Nazwa zawodnika nie może być pusta.")
                    return
                if nowa_nazwa != nazwa and nowa_nazwa in self.zawodnicy:
                    messagebox.showwarning("Błąd", "Zawodnik o tej nazwie już istnieje.")
                    return
                # Aktualizacja nazwy zawodnika
                if nowa_nazwa != nazwa:
                    zawodnik.nazwa = nowa_nazwa
                    del self.zawodnicy[nazwa]
                    self.zawodnicy[nowa_nazwa] = zawodnik
                edit_window.destroy()
                self.odswiez_listy_zawodnikow()
                self.pokaz_klasyfikacje()
                messagebox.showinfo("Sukces", f"Zaktualizowano zawodnika '{nowa_nazwa}'.")

            ttk.Button(edit_window, text="Zapisz", command=zapisz_zmiany).grid(
                row=1, column=0, columnspan=2, padx=5, pady=10
            )
        else:
            messagebox.showwarning("Błąd", "Nie wybrano zawodnika do edycji.")

    def importuj_zawodnikow(self):
        filepath = filedialog.askopenfilename(
            title="Wybierz plik CSV z zawodnikami",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")),
        )
        if filepath:
            try:
                with open(filepath, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        nazwa = row['Nazwa']
                        rating = float(row['Rating'])
                        rd = float(row['RD'])
                        vol = float(row['Volatility'])
                        if nazwa in self.zawodnicy:
                            messagebox.showwarning(
                                "Błąd",
                                f"Zawodnik '{nazwa}' już istnieje. Pomijam import tego zawodnika.",
                            )
                            continue
                        zawodnik = Zawodnik(nazwa, rating, rd, vol)
                        self.zawodnicy[nazwa] = zawodnik
                self.odswiez_listy_zawodnikow()
                self.pokaz_klasyfikacje()
                messagebox.showinfo("Sukces", "Zaimportowano zawodników.")
            except Exception as e:
                messagebox.showerror(
                    "Błąd", f"Błąd podczas importu zawodników: {e}"
                )

    def eksportuj_zawodnikow(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")),
            title="Zapisz jako",
        )
        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        "Nazwa",
                        "Rating",
                        "RD",
                        "Volatility",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for zawodnik in self.zawodnicy.values():
                        writer.writerow(
                            {
                                "Nazwa": zawodnik.nazwa,
                                "Rating": f"{zawodnik.player.rating:.2f}",
                                "RD": f"{zawodnik.player.rd:.2f}",
                                "Volatility": f"{zawodnik.player.vol:.5f}",
                            }
                        )
                messagebox.showinfo("Sukces", "Zawodnicy zostali wyeksportowani.")
            except Exception as e:
                messagebox.showerror(
                    "Błąd", f"Błąd podczas eksportu zawodników: {e}"
                )

    def zaznacz_zawodnika(self, event):
        pass  # Możesz dodać dodatkowe akcje po zaznaczeniu zawodnika

    # Metody obsługi meczów
    def rozegrac_mecz_gui(self):
        nazwa1 = self.var_player1.get()
        nazwa2 = self.var_player2.get()
        wynik_str = self.var_result.get()

        # Sprawdzenie, czy wybrano dwóch różnych zawodników
        if nazwa1 and nazwa2 and nazwa1 != nazwa2:
            # Przypisanie wyników w formacie liczbowym
            if wynik_str == "Wygrana Zawodnika 1":
                wynik1 = 1
                wynik2 = 0
                # Aktualizacja statystyk
                self.zawodnicy[nazwa1].wygrane += 1
                self.zawodnicy[nazwa2].przegrane += 1
            elif wynik_str == "Remis":
                wynik1 = 0.5
                wynik2 = 0.5
                # Aktualizacja statystyk
                self.zawodnicy[nazwa1].remisy += 1
                self.zawodnicy[nazwa2].remisy += 1
            else:
                wynik1 = 0
                wynik2 = 1
                # Aktualizacja statystyk
                self.zawodnicy[nazwa1].przegrane += 1
                self.zawodnicy[nazwa2].wygrane += 1

            # Pobranie obiektów zawodników
            zawodnik1 = self.zawodnicy[nazwa1]
            zawodnik2 = self.zawodnicy[nazwa2]

            # Dodanie meczu do listy oponentów każdego zawodnika
            zawodnik1.dodaj_mecz(zawodnik2, wynik1)
            zawodnik2.dodaj_mecz(zawodnik1, wynik2)

            # Automatyczna aktualizacja rankingów po meczu
            self.aktualizuj_rankingi()

            # Dodanie meczu do historii meczów
            data_meczu = datetime.now()
            self.historia_meczow.append(
                {
                    "data": data_meczu.strftime("%Y-%m-%d %H:%M:%S"),
                    "zawodnik1": nazwa1,
                    "zawodnik2": nazwa2,
                    "wynik": wynik_str,
                }
            )

            self.pokaz_klasyfikacje()
            messagebox.showinfo(
                "Sukces", f"Rozegrano mecz między {nazwa1} a {nazwa2}"
            )
        else:
            messagebox.showwarning(
                "Błąd", "Proszę wybrać dwóch różnych zawodników."
            )

    def aktualizuj_rankingi(self):
        for zawodnik in self.zawodnicy.values():
            if zawodnik.oponenci:
                rating_list = []  # Lista ratingów przeciwników
                RD_list = []  # Lista RD przeciwników
                outcome_list = []  # Lista wyników meczów
                for opponent_player, wynik in zawodnik.oponenci:
                    rating_list.append(opponent_player.rating)
                    RD_list.append(opponent_player.rd)
                    outcome_list.append(wynik)
                # Aktualizacja rankingu zawodnika
                zawodnik.player.update_player(
                    rating_list, RD_list, outcome_list
                )
                # Dodanie nowego ratingu do historii
                zawodnik.historia_ratingow.append(zawodnik.player.rating)
                zawodnik.oponenci = []  # Wyczyść listę oponentów po aktualizacji

    def przelicz_rankingi(self):
        # Resetuj statystyki i rankingi zawodników
        for zawodnik in self.zawodnicy.values():
            zawodnik.player = Player()
            zawodnik.wygrane = 0
            zawodnik.przegrane = 0
            zawodnik.remisy = 0
            zawodnik.historia_ratingow = [zawodnik.player.rating]
            zawodnik.oponenci = []

        # Przejdź przez historię meczów i zaktualizuj statystyki
        for mecz in sorted(self.historia_meczow, key=lambda x: x['data']):
            nazwa1 = mecz['zawodnik1']
            nazwa2 = mecz['zawodnik2']
            wynik_str = mecz['wynik']

            if nazwa1 not in self.zawodnicy or nazwa2 not in self.zawodnicy:
                continue

            # Przypisanie wyników w formacie liczbowym
            if wynik_str == "Wygrana Zawodnika 1":
                wynik1 = 1
                wynik2 = 0
                # Aktualizacja statystyk
                self.zawodnicy[nazwa1].wygrane += 1
                self.zawodnicy[nazwa2].przegrane += 1
            elif wynik_str == "Remis":
                wynik1 = 0.5
                wynik2 = 0.5
                # Aktualizacja statystyk
                self.zawodnicy[nazwa1].remisy += 1
                self.zawodnicy[nazwa2].remisy += 1
            else:
                wynik1 = 0
                wynik2 = 1
                # Aktualizacja statystyk
                self.zawodnicy[nazwa1].przegrane += 1
                self.zawodnicy[nazwa2].wygrane += 1

            # Dodanie meczu do listy oponentów każdego zawodnika
            zawodnik1 = self.zawodnicy[nazwa1]
            zawodnik2 = self.zawodnicy[nazwa2]
            zawodnik1.dodaj_mecz(zawodnik2, wynik1)
            zawodnik2.dodaj_mecz(zawodnik1, wynik2)

            # Aktualizacja rankingów po każdej rundzie
            self.aktualizuj_rankingi()

    def importuj_mecze(self):
        filepath = filedialog.askopenfilename(
            title="Wybierz plik CSV z meczami",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")),
        )
        if filepath:
            try:
                with open(filepath, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    imported_matches = []
                    for row in reader:
                        data = row['Data']
                        zawodnik1 = row['Zawodnik1']
                        zawodnik2 = row['Zawodnik2']
                        wynik = row['Wynik']
                        # Sprawdzenie, czy zawodnicy istnieją
                        if zawodnik1 not in self.zawodnicy or zawodnik2 not in self.zawodnicy:
                            messagebox.showwarning(
                                "Błąd",
                                f"Mecz pomiędzy {zawodnik1} a {zawodnik2} został pominięty, "
                                "ponieważ jeden z zawodników nie istnieje.",
                            )
                            continue
                        imported_matches.append({
                            "data": data,
                            "zawodnik1": zawodnik1,
                            "zawodnik2": zawodnik2,
                            "wynik": wynik,
                        })
                    # Dodanie meczów do historii
                    self.historia_meczow.extend(imported_matches)
                    # Aktualizacja statystyk i rankingów
                    self.przelicz_rankingi()
                    self.pokaz_klasyfikacje()
                    messagebox.showinfo("Sukces", "Zaimportowano historię meczów.")
            except Exception as e:
                messagebox.showerror(
                    "Błąd", f"Błąd podczas importu meczów: {e}"
                )

    def eksportuj_mecze(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")),
            title="Zapisz jako",
        )
        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Data', 'Zawodnik1', 'Zawodnik2', 'Wynik']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for mecz in self.historia_meczow:
                        writer.writerow({
                            'Data': mecz['data'],
                            'Zawodnik1': mecz['zawodnik1'],
                            'Zawodnik2': mecz['zawodnik2'],
                            'Wynik': mecz['wynik'],
                        })
                messagebox.showinfo("Sukces", "Historia meczów została wyeksportowana.")
            except Exception as e:
                messagebox.showerror(
                    "Błąd", f"Błąd podczas eksportu meczów: {e}"
                )

    # Metody obsługi klasyfikacji
    def pokaz_klasyfikacje(self):
        self.tree.delete(*self.tree.get_children())

        # Pobierz dane do tabeli
        tabela = self.generuj_tabele_klasyfikacji()

        for wpis in tabela:
            self.tree.insert("", tk.END, values=(
                wpis["pozycja"],
                wpis["zawodnik"].nazwa,
                f"{wpis['ranking']:.2f}",
                f"{wpis['procent_wygranych']:.2f}%",
                f"{wpis['punkty_na_gre']:.2f}",
                f"{wpis['punkty']:.1f}",
                wpis["liczba_gier"],
                wpis["wygrane"],
                wpis["remisy"],
                wpis["przegrane"],
            ))

    def generuj_tabele_klasyfikacji(self):
        tabela = []
        for zawodnik in self.zawodnicy.values():
            mecze = zawodnik.wygrane + zawodnik.przegrane + zawodnik.remisy
            punkty = zawodnik.wygrane + 0.5 * zawodnik.remisy
            if mecze > 0:
                procent_wygranych = (zawodnik.wygrane / mecze) * 100
                punkty_na_gre = punkty / mecze
            else:
                procent_wygranych = 0
                punkty_na_gre = 0

            wpis = {
                "zawodnik": zawodnik,
                "ranking": zawodnik.player.rating,
                "punkty": punkty,
                "punkty_na_gre": punkty_na_gre,
                "procent_wygranych": procent_wygranych,
                "wygrane": zawodnik.wygrane,
                "remisy": zawodnik.remisy,
                "przegrane": zawodnik.przegrane,
                "liczba_gier": mecze,
            }
            tabela.append(wpis)

        # Sortowanie tabeli według podanych kryteriów
        tabela.sort(key=self.get_sort_key)

        # Ustawienie pozycji
        for idx, wpis in enumerate(tabela, start=1):
            wpis["pozycja"] = idx

        return tabela

    def get_sort_key(self, wpis):
        # Implementacja reguł rozstrzygania remisów
        return (
            -wpis["ranking"],  # RANKING malejąco
            -wpis["punkty"],  # LICZBA PUNKTÓW malejąco
            -wpis["punkty_na_gre"],  # LICZBA PUNKTÓW/GIER malejąco
            -wpis["procent_wygranych"],  # %WYGRANYCH malejąco
            -wpis["wygrane"],  # WYGRANE malejąco
            -wpis["remisy"],  # REMISY malejąco
            wpis["przegrane"],  # PRZEGRANE rosnąco (mniej przegranych lepsze)
        )

    def odswiez_dane_zawodnika(self, event=None):
        nazwa = self.var_selected_player.get()
        if nazwa in self.zawodnicy:
            pass  # Możesz dodać dodatkowe akcje po wyborze zawodnika

    def pokaz_historia_meczow_zawodnika(self):
        nazwa = self.var_selected_player.get()
        if nazwa in self.zawodnicy:
            historia_window = tk.Toplevel(self.root)
            historia_window.title(f"Historia Meczów - {nazwa}")

            text_historia = tk.Text(historia_window, wrap=tk.WORD)
            text_historia.pack(fill=tk.BOTH, expand=True)

            # Wypełnienie pola tekstowego informacjami o meczach
            for mecz in self.historia_meczow:
                if mecz['zawodnik1'] == nazwa or mecz['zawodnik2'] == nazwa:
                    info = (
                        f"{mecz['data']}: {mecz['zawodnik1']} vs {mecz['zawodnik2']} - "
                        f"Wynik: {mecz['wynik']}\n"
                    )
                    text_historia.insert(tk.END, info)
        else:
            messagebox.showwarning("Błąd", "Wybierz zawodnika z listy.")

    def pokaz_wykres_zawodnika(self):
        nazwa = self.var_selected_player.get()
        if nazwa in self.zawodnicy:
            zawodnik = self.zawodnicy[nazwa]
            if len(zawodnik.historia_ratingow) < 2:
                messagebox.showwarning(
                    "Błąd", "Zbyt mało danych, aby wyświetlić wykres."
                )
                return
            # Przygotowanie danych
            x_values = list(range(len(zawodnik.historia_ratingow)))
            y_values = zawodnik.historia_ratingow
            plt.figure()
            plt.plot(x_values, y_values, marker='o', label=nazwa)
            plt.title(f"Zmiana ratingu zawodnika {nazwa}")
            plt.xlabel("Numer gry")
            plt.ylabel("Rating")
            plt.xticks(x_values)
            plt.grid(True)
            plt.legend()
            plt.show()
        else:
            messagebox.showwarning("Błąd", "Wybierz zawodnika z listy.")

    # Metody zapisu i wczytywania danych
    def zapisz_dane(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pkl",
            filetypes=(("Pickle Files", "*.pkl"), ("All Files", "*.*")),
            title="Zapisz jako",
        )
        if filepath:
            try:
                data = {
                    "zawodnicy": {
                        nazwa: zawodnik.get_state()
                        for nazwa, zawodnik in self.zawodnicy.items()
                    },
                    "historia_meczow": self.historia_meczow,
                }
                with open(filepath, "wb") as f:
                    pickle.dump(data, f)
                messagebox.showinfo("Sukces", "Dane zostały zapisane.")
            except Exception as e:
                messagebox.showerror(
                    "Błąd", f"Błąd podczas zapisywania danych: {e}"
                )

    def wczytaj_dane(self):
        filepath = filedialog.askopenfilename(
            title="Wybierz plik z danymi",
            filetypes=(("Pickle Files", "*.pkl"), ("All Files", "*.*")),
        )
        if filepath:
            try:
                with open(filepath, "rb") as f:
                    data = pickle.load(f)
                self.zawodnicy = {
                    nazwa: Zawodnik.from_state(state)
                    for nazwa, state in data.get("zawodnicy", {}).items()
                }
                self.historia_meczow = data.get("historia_meczow", [])
                self.odswiez_listy_zawodnikow()
                # Przelicz rankingi na podstawie wczytanej historii meczów
                self.przelicz_rankingi()
                self.pokaz_klasyfikacje()
                messagebox.showinfo("Sukces", "Dane zostały wczytane.")
            except FileNotFoundError:
                messagebox.showwarning(
                    "Błąd", "Plik z danymi nie istnieje."
                )
            except Exception as e:
                messagebox.showerror(
                    "Błąd", f"Błąd podczas wczytywania danych: {e}"
                )

    def eksportuj_rankingi(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")),
            title="Zapisz jako",
        )
        if filepath:
            try:
                with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                    fieldnames = [
                        "Nazwa",
                        "Rating",
                        "RD",
                        "Volatility",
                        "Wygrane",
                        "Przegrane",
                        "Remisy",
                        "Procent Wygranych",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for nazwa, zawodnik in self.zawodnicy.items():
                        rating = zawodnik.player.rating
                        rd = zawodnik.player.rd
                        vol = zawodnik.player.vol
                        mecze = (
                            zawodnik.wygrane
                            + zawodnik.przegrane
                            + zawodnik.remisy
                        )
                        if mecze > 0:
                            procent_wygranych = (
                                (zawodnik.wygrane / mecze) * 100
                            )
                        else:
                            procent_wygranych = 0
                        writer.writerow(
                            {
                                "Nazwa": nazwa,
                                "Rating": f"{rating:.2f}",
                                "RD": f"{rd:.2f}",
                                "Volatility": f"{vol:.5f}",
                                "Wygrane": zawodnik.wygrane,
                                "Przegrane": zawodnik.przegrane,
                                "Remisy": zawodnik.remisy,
                                "Procent Wygranych": f"{procent_wygranych:.2f}%",
                            }
                        )
                messagebox.showinfo(
                    "Sukces", "Rankingi zostały wyeksportowane."
                )
            except Exception as e:
                messagebox.showerror(
                    "Błąd", f"Błąd podczas eksportu rankingów: {e}"
                )


def main():
    root = tk.Tk()
    app = Aplikacja(root)
    root.mainloop()


if __name__ == "__main__":
    main()
