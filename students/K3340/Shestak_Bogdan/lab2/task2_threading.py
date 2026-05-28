import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
 
import psycopg2
 
#Настройки БД
DB_CONFIG = {
    "dbname": "finance_db",
    "user": "postgres",
    "password": "8118",
    "host": "localhost",
    "port": 5432,
}
 
DATES = [
    "30/04/2026",
    "01/05/2026",
    "02/05/2026",
    "03/05/2026",
    "04/05/2026",
    "05/05/2026",
    "06/05/2026",
    "07/05/2026",
]
 
BASE_URL = "https://www.cbr.ru/scripts/XML_daily.asp?date_req={}"
NUM_THREADS = 4
 
db_lock = threading.Lock()
 
 
def fetch_rates(date_str: str) -> list[dict]:
    """
    Загружает XML с курсами ЦБ РФ на указанную дату.
    Возвращает список: [{"currency_code", "currency_name", "rate", "date"}, ...]
    """
    url = BASE_URL.format(date_str)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read()
 
        root = ET.fromstring(xml_data)
        raw_date = root.attrib.get("Date", date_str.replace("/", "."))
        d, m, y = raw_date.split(".")
        parsed_date = date(int(y), int(m), int(d))
 
        rates = []
        for valute in root.findall("Valute"):
            code = valute.findtext("CharCode", "").strip()
            name = valute.findtext("Name", "").strip()
            nominal = int(valute.findtext("Nominal", "1").strip())
            value_str = valute.findtext("Value", "0").strip().replace(",", ".")
            rate = round(float(value_str) / nominal, 4)
            rates.append({
                "currency_code": code,
                "currency_name": name,
                "rate": rate,
                "date": parsed_date,
            })
        return rates
 
    except Exception as e:
        print(f"[threading] Ошибка при загрузке {date_str}: {e}")
        return []
 
 
def save_rates(conn, rates: list[dict]) -> None:
    """Сохраняет список курсов в таблицу exchange_rate."""
    with conn.cursor() as cur:
        for r in rates:
            cur.execute(
                """
                INSERT INTO exchange_rate (currency_code, currency_name, rate, date)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (currency_code, date)
                DO UPDATE SET rate = EXCLUDED.rate, currency_name = EXCLUDED.currency_name
                """,
                (r["currency_code"], r["currency_name"], r["rate"], r["date"]),
            )
    conn.commit()
 
 
def parse_and_save(date_str: str, conn) -> None:
    """Парсит курсы на дату и сохраняет в БД."""
    rates = fetch_rates(date_str)
    if not rates:
        return
    print(f"[threading] {date_str} — получено {len(rates)} курсов")
    with db_lock:
        save_rates(conn, rates)
 
 
def ensure_table(conn) -> None:
    """Создаёт таблицу exchange_rate, если её нет."""
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS exchange_rate (
                id            SERIAL PRIMARY KEY,
                currency_code VARCHAR(10)    NOT NULL,
                currency_name TEXT           NOT NULL,
                rate          NUMERIC(18, 4) NOT NULL,
                date          DATE           NOT NULL,
                UNIQUE (currency_code, date)
            )
            """
        )
    conn.commit()
 
 
def main():
    conn = psycopg2.connect(**DB_CONFIG)
    ensure_table(conn)
 
    threads = []
    start_time = time.perf_counter()
 
    for date_str in DATES:
        t = threading.Thread(target=parse_and_save, args=(date_str, conn))
        threads.append(t)
        t.start()
 
    for t in threads:
        t.join()
 
    elapsed = time.perf_counter() - start_time
    print(f"\n[threading] Готово. Время: {elapsed:.4f} сек")
    conn.close()
 
 
if __name__ == "__main__":
    main()