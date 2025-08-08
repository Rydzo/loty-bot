import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from db import save_flight

def search_and_save_flight_data(origin: str, destination: str, days_forward: int):
    today = datetime.today()
    return_date = today + timedelta(days=days_forward)
    today_str = today.strftime("%d.%m.%Y")
    return_str = return_date.strftime("%d.%m.%Y")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1) Wejdź na stronę
        for attempt in range(3):
            try:
                page.goto("https://www.azair.eu/", timeout=30000, wait_until="networkidle")
                break
            except PlaywrightTimeout:
                if attempt == 2:
                    print(f"❌ [{origin} → {destination}] Nie udało się wczytać strony.")
                    browser.close()
                    return
                print("⚠️ Timeout podczas ładowania, ponawiam...")

        # 2) Cookies + waluta
        try:
            page.locator("button[aria-label='Zgadzam się']").click(timeout=3000)
        except:
            pass
        try:
            page.select_option("select[name='currency']", value="PLN")
        except:
            pass

        # 3) Formularz – czyszczenie + wpis + Tab
        src = page.locator("input[name='srcAirport']")
        src.click()
        src.press("Control+A")
        src.press("Delete")
        src.type(origin, delay=50)
        src.press("Tab")

        dst = page.locator("input[name='dstAirport']")
        dst.click()
        dst.press("Control+A")
        dst.press("Delete")
        dst.type(destination, delay=50)
        dst.press("Tab")

        page.locator("input[name='depdate']").evaluate("(el, v) => el.value = v", today_str)
        page.locator("input[name='arrdate']").evaluate("(el, v) => el.value = v", return_str)
        page.fill("input[name='minDaysStay']", "3")
        page.fill("input[name='maxDaysStay']", "7")

        # 4) Kliknij SEARCH i zamknij banner cookies
        page.locator("input[type='submit'][value*='Search']").click()
        try:
            page.locator("text=Nie zgadzam się").click(timeout=5000)
        except:
            try:
                page.locator("text=Zgadzam się").click(timeout=5000)
            except:
                pass

        # 5) Czekaj na wyniki
        try:
            page.wait_for_selector("div.result", timeout=60000)
        except PlaywrightTimeout:
            print(f"❌ [{origin} → {destination}] Timeout na wyniki.")
            browser.close()
            return

        # 6) Parsowanie wyników
        results = page.locator("div.result")
        count = results.count()
        print(f"📦 {origin} → {destination} | Znaleziono {count} wyników lotów")

        flights = []
        for i in range(count):
            r = results.nth(i)
            try:
                # Cena
                price_txt = r.locator("span.tp").inner_text()
                price = int(re.sub(r"[^\d]", "", price_txt))

                # Daty: span.date[0] = dep, [1] = return
                dates = r.locator("div.text span.date")
                dep_raw = dates.nth(0).inner_text().split()[1]   # "01/10/25"
                ret_raw = dates.nth(1).inner_text().split()[1]   # "07/10/25"
                d1, m1, y1 = dep_raw.split("/")
                d2, m2, y2 = ret_raw.split("/")
                dep_date = f"{int(d1)}.{int(m1)}.20{y1}"
                ret_date = f"{int(d2)}.{int(m2)}.20{y2}"

                # THERE segment
                there_txt = r.locator("div.text span.from").nth(0).inner_text()
                to_txt    = r.locator("div.text span.to").nth(0).inner_text()
                dep_time, dep_airp = re.match(r".*?(\d{2}:\d{2})\s+(.+?)\s+\w{3}", there_txt).groups()
                arr_time, arr_airp = re.search(r"(\d{2}:\d{2})\s+(.+?)\s+\w{3}", to_txt).groups()

                # BACK segment
                back_txt = r.locator("div.text span.from").nth(1).inner_text()
                ret_to   = r.locator("div.text span.to").nth(1).inner_text()
                ret_time, ret_airp = re.match(r".*?(\d{2}:\d{2})\s+(.+?)\s+\w{3}", ret_to).groups()

                # Filtrowanie długości pobytu
                dep_dt = datetime.strptime(dep_date, "%d.%m.%Y")
                ret_dt = datetime.strptime(ret_date, "%d.%m.%Y")
                stay = (ret_dt - dep_dt).days
                if stay < 3 or stay > 7:
                    continue

                flights.append({
                    "price": price,
                    "origin": origin,
                    "destination": destination,
                    "dep_date": dep_date,
                    "ret_date": ret_date,
                    "depart_time": dep_time,
                    "depart_airport": dep_airp.strip(),
                    "arrive_time": arr_time,
                    "arrive_airport": arr_airp.strip(),
                })
            except Exception as e:
                print(f"⚠️ [{origin} → {destination}] Błąd parsowania #{i}: {e}")

        browser.close()

        # 7) Zapisywanie top 3
        flights.sort(key=lambda x: x["price"])
        for flight in flights[:3]:
            print(f"✈️ {flight['dep_date']} {flight['depart_time']} {flight['depart_airport']} → "
                  f"{flight['ret_date']} {flight['arrive_time']} {flight['arrive_airport']} | Cena: {flight['price']} PLN")
            save_flight(
                flight['depart_airport'].strip(),  # poprawione użycie depart_airport
                flight['destination'],
                flight['dep_date'],
                flight['ret_date'],
                flight['depart_time'],
                flight['depart_airport'],
                flight['arrive_time'],
                flight['arrive_airport'],
                flight['price'],
                "PLN"
            )
