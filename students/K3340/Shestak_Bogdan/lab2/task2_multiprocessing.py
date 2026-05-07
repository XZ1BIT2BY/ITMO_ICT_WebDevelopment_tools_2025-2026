import multiprocessing
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
 
import psycopg2
 
# ── Настройки БД ──────────────────────────────────────────────────────────────
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
NUM_PROCESSES = 4
 
 
def fetch_rates(date_str: str) -> list[dict]:
    """Загружает XML с курсами ЦБ РФ на указанную дату."""
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
        print(f"[multiprocessing] Ошибка при загрузке {date_str}: {e}")
        return []
 
 
def parse_and_save(date_str: str) -> None:
    """
    Парсит курсы на дату и сохраняет в БД.
    Каждый процесс создаёт своё соединение с PostgreSQL.
    """
    rates = fetch_rates(date_str)
    if not rates:
        return
 
    pid = multiprocessing.current_process().pid
    print(f"[multiprocessing] PID={pid} {date_str} — получено {len(rates)} курсов")
 
    try:
        conn = psycopg2.connect(**DB_CONFIG)
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
        conn.close()
    except Exception as e:
        print(f"[multiprocessing] DB ошибка для {date_str}: {e}")
 
 
def ensure_table() -> None:
    """Создаёт таблицу в основном процессе до запуска пула."""
    conn = psycopg2.connect(**DB_CONFIG)
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
    conn.close()
 
 
def main():
    ensure_table()
 
    start_time = time.perf_counter()
 
    with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
        pool.map(parse_and_save, DATES)
 
    elapsed = time.perf_counter() - start_time
    print(f"\n[multiprocessing] Готово. Время: {elapsed:.4f} сек")
 
 
if __name__ == "__main__":
    main()