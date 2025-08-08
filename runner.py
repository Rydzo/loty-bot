# runner.py
import time
from db import init_db, save_flight
from scraper import search_and_save_flight_data

# 1) Polska lotniska źródłowe
POLISH_AIRPORTS = [
    "Poland",
]

# 2) Wczytaj Top100 destynacji
with open("top100.txt", encoding="utf-8") as f:
    DESTINATIONS = [line.strip() for line in f if line.strip()]

# 3) Zakres wyszukiwań (dni do przodu)
DAYS_FORWARD = 180

if __name__ == "__main__":
    # 0) Inicjalizacja bazy danych
    init_db()

    # 4) Pętla główna
    for origin in POLISH_AIRPORTS:
        for dest in DESTINATIONS:
            print(f"\n🔎 Scraping: {origin} → {dest}")
            try:
                search_and_save_flight_data(origin, dest, DAYS_FORWARD)
                print("✅ Zapisano dane")
            except Exception as e:
                print(f"❌ Błąd przy {origin}->{dest}: {e}")
            # 5 sekund przerwy między kolejnymi zapytaniami
            time.sleep(5)
