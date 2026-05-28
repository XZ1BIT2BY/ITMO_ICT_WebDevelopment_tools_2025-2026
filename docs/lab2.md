# Лабораторная работа 2 — Потоки, процессы и асинхронность
 
## Описание
Сравнение трёх подходов к параллельному выполнению задач в Python: `threading`, `multiprocessing` и `asyncio`. Реализованы два задания: вычисление суммы чисел и параллельный парсинг курсов валют с сохранением в БД.
 
## Теория
 
### GIL (Global Interpreter Lock)
Мьютекс в CPython, не позволяющий нескольким потокам одновременно исполнять байткод. Из-за GIL `threading` не даёт ускорения для CPU-bound задач, но эффективен для I/O-bound — поток освобождает GIL во время ожидания ответа от сети или диска.
 
### Сравнение подходов
 
| Характеристика     | `threading`      | `multiprocessing`  | `asyncio`              |
|--------------------|------------------|--------------------|------------------------|
| Параллелизм        | Псевдо (GIL)     | Настоящий          | Конкурентность (1 поток)|
| Память             | Общая            | Раздельная         | Общая                  |
| Накладные расходы  | Низкие           | Высокие            | Минимальные            |
| Лучшая область     | I/O-bound        | CPU-bound          | I/O-bound              |
 
## Задача 1 — Вычисление суммы чисел от 1 до 10^10
 
Каждая программа делит диапазон на 8 равных частей и считает сумму параллельно.
 
### threading
 
```python
def calculate_sum(start: int, end: int, results: list, index: int) -> None:
    total = 0
    for i in range(start, end):
        total += i
    results[index] = total
```
 
Потоки работают через `threading.Thread`. Из-за GIL реального параллелизма нет — время сопоставимо с однопоточным.
 
### multiprocessing
 
```python
def calculate_sum(start: int, end: int) -> int:
    total = 0
    for i in range(start, end):
        total += i
    return total
```
 
Используется `multiprocessing.Pool.starmap()`. Каждый процесс работает в отдельном интерпретаторе без GIL — настоящий параллелизм.
 
### asyncio
 
```python
async def calculate_sum_async(executor, start: int, end: int) -> int:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, calculate_sum, start, end)
```
 
Синхронная функция запускается через `ProcessPoolExecutor`. `asyncio.gather()` конкурентно ожидает все корутины.
 
### Результаты
 
| Подход          | Время выполнения | Ускорение           |
|-----------------|-----------------|----------------------|
| threading       | 589.98 сек      | 1× (GIL)             |
| multiprocessing | 119.43 сек      | ~4.9×                |
| asyncio + Pool  | 123.18 сек      | ~4.8×                |
 
## Задача 2 — Параллельный парсинг курсов валют
 
Парсинг курсов валют с сайта ЦБ РФ (`cbr.ru`) за 8 дат с сохранением в таблицу `exchange_rate` базы данных PostgreSQL из лабораторной работы №1.
 
### Схема таблицы
 
```sql
CREATE TABLE IF NOT EXISTS exchange_rate (
    id            SERIAL PRIMARY KEY,
    currency_code VARCHAR(10)    NOT NULL,
    currency_name TEXT           NOT NULL,
    rate          NUMERIC(18, 4) NOT NULL,
    date          DATE           NOT NULL,
    UNIQUE (currency_code, date)
);
```
 
### threading
 
Каждый поток выполняет `parse_and_save(date_str, conn)`. Общее соединение с БД защищено `threading.Lock` — потоки записывают данные по очереди.
 
### multiprocessing
 
Каждый процесс открывает собственное соединение с БД — объекты `psycopg2` не сериализуемы и не передаются между процессами.
 
### asyncio
 
`aiohttp.ClientSession` для асинхронных HTTP-запросов, `asyncpg.Pool` для асинхронной работы с PostgreSQL. `asyncio.gather()` запускает все корутины конкурентно в одном потоке.
 
### Результаты
 
| Подход          | Время выполнения |
|-----------------|-----------------|
| asyncio         | 0.11 сек        |
| threading       | 1.27 сек        |
| multiprocessing | 3.86 сек        |
 
## Выводы
 
Для **CPU-bound** задач единственный эффективный вариант — `multiprocessing`: он обходит GIL и задействует все ядра CPU. `threading` из-за GIL не даёт ускорения.
 
Для **I/O-bound** задач лучший выбор — `asyncio`: минимальные накладные расходы и максимальный параллелизм в одном потоке. `threading` тоже эффективен. `multiprocessing` избыточен — накладные расходы на запуск процессов перевешивают выигрыш.
 
| Тип задачи | Рекомендация                      |
|------------|-----------------------------------|
| CPU-bound  | `multiprocessing`                 |
| I/O-bound  | `asyncio` или `threading`         |
| Смешанная  | `asyncio` + `ProcessPoolExecutor` |
 
## Ссылки
- [Код лабораторной](https://github.com/XZ1BIT2BY/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lab2/students/K3340/Shestak_Bogdan/lab2)