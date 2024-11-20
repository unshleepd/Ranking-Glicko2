# glicko.py
# -*- coding: utf-8 -*-

"""
Aplikacja do zarządzania rankingami zawodników w systemie Glicko-2 z interfejsem
graficznym (GUI) opartym na bibliotece Tkinter. Umożliwia dodawanie zawodników,
rozgrywanie meczów, automatyczną aktualizację rankingów, wyświetlanie historii
meczów, tworzenie wykresów zmian rankingów oraz eksportowanie danych.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import pickle
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import re
from glicko2 import Player


class Zawodnik:
    """
    Klasa reprezentująca zawodnika w systemie rankingowym Glicko-2.

    Attributes:
        nazwa (str): Nazwa zawodnika.
        player (Player): Obiekt Player z biblioteki glicko2 przechowujący dane
            rankingowe.
        oponenci (list): Lista przeciwników i wyników meczów do aktualizacji
            rankingu.
        wygrane (int): Liczba wygranych meczów.
        przegrane (int): Liczba przegranych meczów.
        remisy (int): Liczba remisów.
        historia_ratingow (list): Historia ratingów po każdej aktualizacji.
    """

    def __init__(self, nazwa, rating=None, rd=None, vol=None):
        """
        Inicjalizuje nowego zawodnika.

        Args:
            nazwa (str): Nazwa zawodnika.
            rating (float, optional): Początkowy rating zawodnika. Jeśli None,
                używany jest domyślny.
            rd (float, optional): Początkowa wartość RD zawodnika. Jeśli None,
                używany jest domyślny.
            vol (float, optional): Początkowa wartość volatility zawodnika.
                Jeśli None, używany jest domyślny.
        """
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

    def dodaj_mecz(self, przeciwnik, wynik):
        """
        Dodaje mecz do listy oponentów do aktualizacji rankingu.

        Args:
            przeciwnik (Zawodnik): Przeciwnik w meczu.
            wynik (float): Wynik meczu (1 - wygrana, 0.5 - remis, 0 - przegrana).
        """
        self.oponenci.append((przeciwnik.player, wynik))

    def get_state(self):
        """
        Przygotowuje stan obiektu do zapisu (serializacji).

        Returns:
            dict: Słownik zawierający stan obiektu.
        """
        state = {
            "nazwa": self.nazwa,
            "rating": self.player.rating,
            "rd": self.player.rd,
            "vol": self.player.vol,
            "wygrane": self.wygrane,
            "przegrane": self.przegrane,
            "remisy": self.remisy,
            "historia_ratingow": self.historia_ratingow,
        }
        return state

    @classmethod
    def from_state(cls, state):
        """
        Odtwarza obiekt Zawodnik ze stanu (deserializacja).

        Args:
            state (dict): Słownik zawierający stan obiektu.

        Returns:
            Zawodnik: Nowy obiekt Zawodnik odtworzony ze stanu.
        """
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
        return zawodnik


class Aplikacja:
    """
    Klasa reprezentująca główną aplikację GUI do zarządzania rankingami zawodników.
    """

    def __init__(self, root):
        """
        Inicjalizuje aplikację.

        Args:
            root (tk.Tk): Główne okno aplikacji.
        """
        self.root = root
        self.root.title("Ranking Glicko-2")

        self.zawodnicy = {}
        self.historia_meczow = []

        # Ustawienie motywu na "clam" (minimalistyczny i czytelny)
        style = ttk.Style()
        style.theme_use("clam")

        self.tworz_widgets()

    def tworz_widgets(self):
        """
        Tworzy interfejs użytkownika (widgety).
        """
        # Tworzenie menu
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Menu "Plik" z opcjami "Zapisz", "Wczytaj" i "Wyjście"
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Plik", menu=file_menu)
        file_menu.add_command(label="Zapisz", command=self.zapisz_dane)
        file_menu.add_command(label="Wczytaj", command=self.wczytaj_dane)
        file_menu.add_separator()
        file_menu.add_command(label="Wyjście", command=self.root.quit)

        # Główny frame aplikacji
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Sekcja dodawania zawodników
        add_player_frame = ttk.LabelFrame(
            main_frame, text="Dodaj Zawodnika", padding="10"
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

        # Sekcja rozgrywania meczów
        play_match_frame = ttk.LabelFrame(
            main_frame, text="Rozegraj Mecz", padding="10"
        )
        play_match_frame.pack(fill=tk.X, pady=5)

        # Wybór zawodnika 1
        ttk.Label(play_match_frame, text="Zawodnik 1:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.var_player1 = tk.StringVar()
        self.combo_player1 = ttk.Combobox(
            play_match_frame, textvariable=self.var_player1, state="readonly"
        )
        self.combo_player1.grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )

        # Wybór zawodnika 2
        ttk.Label(play_match_frame, text="Zawodnik 2:").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.var_player2 = tk.StringVar()
        self.combo_player2 = ttk.Combobox(
            play_match_frame, textvariable=self.var_player2, state="readonly"
        )
        self.combo_player2.grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )

        # Wybór wyniku meczu
        ttk.Label(play_match_frame, text="Wynik:").grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.var_result = tk.StringVar(value="Wygrana Zawodnika 1")
        self.combo_result = ttk.Combobox(
            play_match_frame,
            textvariable=self.var_result,
            values=["Wygrana Zawodnika 1", "Remis", "Wygrana Zawodnika 2"],
            state="readonly",
        )
        self.combo_result.grid(
            row=2, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )

        # Przycisk "Rozegraj Mecz"
        play_button = ttk.Button(
            play_match_frame, text="Rozegraj Mecz", command=self.rozegrac_mecz_gui
        )
        play_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        play_match_frame.columnconfigure(1, weight=1)

        # Sekcja sortowania rankingów
        sort_frame = ttk.Frame(main_frame)
        sort_frame.pack(fill=tk.X, pady=5)

        # Opcje sortowania
        ttk.Label(sort_frame, text="Sortuj według:").pack(side=tk.LEFT, padx=5)
        self.var_sort = tk.StringVar(value="Rating")
        sort_options = ["Rating", "Procent wygranych", "Liczba meczów"]
        sort_menu = ttk.OptionMenu(
            sort_frame, self.var_sort, sort_options[0], *sort_options
        )
        sort_menu.pack(side=tk.LEFT, padx=5)

        # Sekcja akcji (przyciski)
        action_frame = ttk.Frame(main_frame, padding="10")
        action_frame.pack(fill=tk.X, pady=5)

        # Przycisk "Pokaż Rankingi"
        show_button = ttk.Button(
            action_frame, text="Pokaż Rankingi", command=self.pokaz_rankingi
        )
        show_button.pack(side=tk.LEFT, padx=5)

        # Przycisk "Eksportuj Rankingi"
        export_button = ttk.Button(
            action_frame, text="Eksportuj Rankingi", command=self.eksportuj_rankingi
        )
        export_button.pack(side=tk.LEFT, padx=5)

        # Przycisk "Pokaż Historię Meczów"
        historia_button = ttk.Button(
            action_frame,
            text="Pokaż Historię Meczów",
            command=self.pokaz_historia_meczow,
        )
        historia_button.pack(side=tk.LEFT, padx=5)

        # Przycisk "Pokaż Wykres"
        plot_button = ttk.Button(
            action_frame, text="Pokaż Wykres", command=self.pokaz_wykres
        )
        plot_button.pack(side=tk.LEFT, padx=5)

        # Sekcja wyświetlania rankingów
        ranking_frame = ttk.LabelFrame(
            main_frame, text="Rankingi", padding="10"
        )
        ranking_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Pole tekstowe do wyświetlania rankingów
        self.text_output = tk.Text(ranking_frame, height=10, wrap=tk.WORD)
        self.text_output.pack(fill=tk.BOTH, expand=True)

        # Dodanie paska przewijania do pola tekstowego
        scrollbar = ttk.Scrollbar(
            self.text_output, command=self.text_output.yview
        )
        self.text_output.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def dodaj_zawodnika_gui(self):
        """
        Obsługuje dodawanie nowego zawodnika przez interfejs GUI.
        """
        nazwa = self.entry_player_name.get().strip()
        if nazwa:
            # Walidacja nazwy zawodnika (dozwolone znaki i długość)
            if not re.match("^[A-Za-z0-9_ ]{1,20}$", nazwa):
                messagebox.showwarning(
                    "Błąd",
                    "Nazwa zawodnika zawiera niedozwolone znaki lub jest za długa.",
                )
                return
            if nazwa not in self.zawodnicy:
                # Dodanie nowego zawodnika do słownika
                self.zawodnicy[nazwa] = Zawodnik(nazwa)
                self.entry_player_name.delete(0, tk.END)  # Wyczyść pole tekstowe
                self.odswiez_listy_zawodnikow()  # Odśwież listy zawodników w interfejsie
                messagebox.showinfo("Sukces", f"Dodano zawodnika {nazwa}")
            else:
                messagebox.showwarning(
                    "Błąd", f"Zawodnik {nazwa} już istnieje."
                )
        else:
            messagebox.showwarning(
                "Błąd", "Nazwa zawodnika nie może być pusta."
            )

    def odswiez_listy_zawodnikow(self):
        """
        Aktualizuje listy zawodników w comboboxach.
        """
        zawodnicy_list = list(self.zawodnicy.keys())
        self.combo_player1["values"] = zawodnicy_list
        self.combo_player2["values"] = zawodnicy_list

    def rozegrac_mecz_gui(self):
        """
        Obsługuje rozgrywanie meczu między zawodnikami przez interfejs GUI.
        """
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
            self.historia_meczow.append(
                {
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "zawodnik1": nazwa1,
                    "zawodnik2": nazwa2,
                    "wynik": wynik_str,
                }
            )

            messagebox.showinfo(
                "Sukces", f"Rozegrano mecz między {nazwa1} a {nazwa2}"
            )
        else:
            messagebox.showwarning(
                "Błąd", "Proszę wybrać dwóch różnych zawodników."
            )

    def aktualizuj_rankingi(self):
        """
        Aktualizuje rankingi wszystkich zawodników na podstawie rozegranych meczów.
        """
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
        # Rankingi są aktualizowane automatycznie po każdym meczu

    def pokaz_rankingi(self):
        """
        Wyświetla rankingi zawodników w polu tekstowym.
        """
        self.text_output.delete(1.0, tk.END)  # Wyczyść pole tekstowe
        sort_key = self.var_sort.get()  # Pobierz wybrane kryterium sortowania

        zawodnicy_list = list(self.zawodnicy.values())

        try:
            # Sortowanie listy zawodników według wybranego kryterium
            if sort_key == "Rating":
                zawodnicy_list.sort(
                    key=lambda x: x.player.rating, reverse=True
                )
            elif sort_key == "Procent wygranych":
                zawodnicy_list.sort(
                    key=lambda x: (x.wygrane / (x.wygrane + x.przegrane + x.remisy))
                    if (x.wygrane + x.przegrane + x.remisy) > 0
                    else 0,
                    reverse=True,
                )
            elif sort_key == "Liczba meczów":
                zawodnicy_list.sort(
                    key=lambda x: x.wygrane + x.przegrane + x.remisy,
                    reverse=True,
                )
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas sortowania: {e}")
            return

        # Wyświetlenie informacji o każdym zawodniku
        for zawodnik in zawodnicy_list:
            rating = zawodnik.player.rating
            rd = zawodnik.player.rd
            vol = zawodnik.player.vol
            mecze = zawodnik.wygrane + zawodnik.przegrane + zawodnik.remisy
            if mecze > 0:
                procent_wygranych = (zawodnik.wygrane / mecze) * 100
            else:
                procent_wygranych = 0
            info = (
                f"{zawodnik.nazwa}:\n"
                f"  Rating: {rating:.2f}, RD: {rd:.2f}, Volatility: {vol:.5f}\n"
                f"  Mecze: {mecze}, Wygrane: {zawodnik.wygrane}, "
                f"Przegrane: {zawodnik.przegrane}, Remisy: {zawodnik.remisy}, "
                f"Procent wygranych: {procent_wygranych:.2f}%\n\n"
            )
            self.text_output.insert(tk.END, info)

    def pokaz_historia_meczow(self):
        """
        Wyświetla historię meczów w nowym oknie.
        """
        historia_window = tk.Toplevel(self.root)
        historia_window.title("Historia Meczów")

        text_historia = tk.Text(historia_window, wrap=tk.WORD)
        text_historia.pack(fill=tk.BOTH, expand=True)

        # Wypełnienie pola tekstowego informacjami o meczach
        for mecz in self.historia_meczow:
            info = (
                f"{mecz['data']}: {mecz['zawodnik1']} vs {mecz['zawodnik2']} - "
                f"Wynik: {mecz['wynik']}\n"
            )
            text_historia.insert(tk.END, info)

    def pokaz_wykres(self):
        """
        Wyświetla wykres zmian ratingu wybranego zawodnika.
        """
        nazwa = self.var_player1.get()
        if nazwa in self.zawodnicy:
            zawodnik = self.zawodnicy[nazwa]
            plt.figure()
            plt.plot(zawodnik.historia_ratingow, marker="o")
            plt.title(f"Zmiana ratingu zawodnika {nazwa}")
            plt.xlabel("Aktualizacje rankingów")
            plt.ylabel("Rating")
            plt.grid(True)
            plt.show()
        else:
            messagebox.showwarning(
                "Błąd", "Wybierz zawodnika z listy."
            )

    def zapisz_dane(self):
        """
        Zapisuje dane zawodników i historii meczów do pliku.
        """
        try:
            data = {
                "zawodnicy": {
                    nazwa: zawodnik.get_state()
                    for nazwa, zawodnik in self.zawodnicy.items()
                },
                "historia_meczow": self.historia_meczow,
            }
            with open("zawodnicy.pkl", "wb") as f:
                pickle.dump(data, f)
            messagebox.showinfo("Sukces", "Dane zostały zapisane.")
        except Exception as e:
            messagebox.showerror(
                "Błąd", f"Błąd podczas zapisywania danych: {e}"
            )

    def wczytaj_dane(self):
        """
        Wczytuje dane zawodników i historii meczów z pliku.
        """
        try:
            with open("zawodnicy.pkl", "rb") as f:
                data = pickle.load(f)
            self.zawodnicy = {
                nazwa: Zawodnik.from_state(state)
                for nazwa, state in data.get("zawodnicy", {}).items()
            }
            self.historia_meczow = data.get("historia_meczow", [])
            self.odswiez_listy_zawodnikow()
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
        """
        Eksportuje rankingi zawodników do pliku CSV.
        """
        try:
            with open(
                "rankingi.csv", "w", newline="", encoding="utf-8"
            ) as csvfile:
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
                "Sukces", "Rankingi zostały wyeksportowane do rankingi.csv"
            )
        except Exception as e:
            messagebox.showerror(
                "Błąd", f"Błąd podczas eksportu rankingów: {e}"
            )


def main():
    """
    Główna funkcja uruchamiająca aplikację.
    """
    root = tk.Tk()
    app = Aplikacja(root)
    root.mainloop()


if __name__ == "__main__":
    main()
