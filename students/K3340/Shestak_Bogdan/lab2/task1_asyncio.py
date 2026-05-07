import asyncio
import time
from concurrent.futures import ProcessPoolExecutor

TOTAL = 10_000_000_000  # 10^10
NUM_WORKERS = 8


def calculate_sum(start: int, end: int) -> int:
    """Считает сумму чисел в диапазоне [start, end). Синхронная функция."""
    total = 0
    for i in range(start, end):
        total += i
    return total


async def calculate_sum_async(executor, start: int, end: int) -> int:
    """Оборачивает синхронную calculate_sum в корутину через executor."""
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, calculate_sum, start, end)
    return result


async def main():
    chunk = TOTAL // NUM_WORKERS
    ranges = []
    for i in range(NUM_WORKERS):
        s = i * chunk + 1
        e = (i + 1) * chunk + 1 if i < NUM_WORKERS - 1 else TOTAL + 1
        ranges.append((s, e))

    start_time = time.perf_counter()

    # ProcessPoolExecutor — чтобы обойти GIL для CPU-bound вычислений
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        tasks = [calculate_sum_async(executor, s, e) for s, e in ranges]
        results = await asyncio.gather(*tasks)

    total_sum = sum(results)
    elapsed = time.perf_counter() - start_time

    expected = TOTAL * (TOTAL + 1) // 2
    print(f"[asyncio] Сумма:    {total_sum}")
    print(f"[asyncio] Ожидалось:{expected}")
    print(f"[asyncio] Совпадает: {total_sum == expected}")
    print(f"[asyncio] Время:    {elapsed:.4f} сек")


if __name__ == "__main__":
    asyncio.run(main())
