import asyncio
import xml.etree.ElementTree as ET
import os
from datetime import date, datetime

import aiohttp
import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Currency Parser Service")

DB_DSN = os.getenv("DATABASE_URL", "postgresql://postgres:8118@db/finance_db")
BASE_URL = "https://www.cbr.ru/scripts/XML_daily.asp?date_req={}"


class ParseRequest(BaseModel):
    date_str: str  # формат: "DD/MM/YYYY", например "28/05/2026"


class ParseResponse(BaseModel):
    message: str
    date: str
    count: int
    rates: list[dict]


async def fetch_rates(session: aiohttp.ClientSession, date_str: str) -> list[dict]:
    """Запрашивает XML с курсами ЦБ РФ на указанную дату."""
    url = BASE_URL.format(date_str)
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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
            "date": str(parsed_date),
        })
    return rates


async def save_rates_to_db(rates: list[dict]) -> None:
    """Сохраняет курсы в таблицу exchange_rate."""
    pool = await asyncpg.create_pool(DB_DSN)
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rate (
                    id            SERIAL PRIMARY KEY,
                    currency_code VARCHAR(10)    NOT NULL,
                    currency_name TEXT           NOT NULL,
                    rate          NUMERIC(18, 4) NOT NULL,
                    date          DATE           NOT NULL,
                    UNIQUE (currency_code, date)
                )
            """)
            await conn.executemany(
                """
                INSERT INTO exchange_rate (currency_code, currency_name, rate, date)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (currency_code, date)
                DO UPDATE SET rate = EXCLUDED.rate, currency_name = EXCLUDED.currency_name
                """,
                [(r["currency_code"], r["currency_name"], r["rate"], date.fromisoformat(r["date"])) for r in rates],
            )
    finally:
        await pool.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
async def parse(request: ParseRequest):
    """
    Парсит курсы ЦБ РФ на указанную дату и сохраняет в БД.
    Формат даты: DD/MM/YYYY, например 28/05/2026
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with aiohttp.ClientSession(headers=headers) as session:
            rates = await fetch_rates(session, request.date_str)

        if not rates:
            raise HTTPException(status_code=502, detail="Не удалось получить данные от ЦБ РФ")

        await save_rates_to_db(rates)

        return ParseResponse(
            message="Парсинг завершён успешно",
            date=request.date_str,
            count=len(rates),
            rates=rates[:10],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parse/today", response_model=ParseResponse)
async def parse_today():
    """Парсит курсы на сегодняшнюю дату."""
    today = datetime.now().strftime("%d/%m/%Y")
    return await parse(ParseRequest(date_str=today))
