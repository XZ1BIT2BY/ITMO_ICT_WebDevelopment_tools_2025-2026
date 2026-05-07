import asyncio
import time
import xml.etree.ElementTree as ET
from datetime import date
 
import aiohttp
import asyncpg
 
# ── Настройки БД ──────────────────────────────────────────────────────────────
DB_DSN = "postgresql://postgres:8118@localhost/finance_db"
 
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
 
 
async def fetch_rates(session: aiohttp.ClientSession, date_str: str) -> list[dict]:
    """Асинхронно загружает XML с курсами ЦБ РФ на указанную дату."""
    url = BASE_URL.format(date_str)
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            xml_data = await resp.read()
 
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
        print(f"[asyncio] Ошибка при загрузке {date_str}: {e}")
        return []
 
 
async def save_rates(pool: asyncpg.Pool, rates: list[dict]) -> None:
    """Асинхронно сохраняет курсы в БД через пул соединений."""
    async with pool.acquire() as conn:
        # executemany для пакетной вставки
        await conn.executemany(
            """
            INSERT INTO exchange_rate (currency_code, currency_name, rate, date)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (currency_code, date)
            DO UPDATE SET rate = EXCLUDED.rate, currency_name = EXCLUDED.currency_name
            """,
            [(r["currency_code"], r["currency_name"], r["rate"], r["date"]) for r in rates],
        )
 
 
async def parse_and_save(
    session: aiohttp.ClientSession, pool: asyncpg.Pool, date_str: str
) -> None:
    """Асинхронно парсит курсы на дату и сохраняет в БД."""
    rates = await fetch_rates(session, date_str)
    if not rates:
        return
    print(f"[asyncio] {date_str} — получено {len(rates)} курсов")
    await save_rates(pool, rates)
 
 
async def ensure_table(pool: asyncpg.Pool) -> None:
    """Создаёт таблицу exchange_rate, если её нет."""
    async with pool.acquire() as conn:
        await conn.execute(
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
 
 
async def main():
    pool = await asyncpg.create_pool(DB_DSN)
    await ensure_table(pool)
 
    start_time = time.perf_counter()
 
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [parse_and_save(session, pool, d) for d in DATES]
        await asyncio.gather(*tasks)
 
    elapsed = time.perf_counter() - start_time
    print(f"\n[asyncio] Готово. Время: {elapsed:.4f} сек")
 
    await pool.close()
 
 
if __name__ == "__main__":
    asyncio.run(main())