import multiprocessing
import time

TOTAL = 10_000_000_000  # 10^10
NUM_PROCESSES = 8


def calculate_sum(start: int, end: int) -> int:
    """Считает сумму чисел в диапазоне [start, end) и возвращает результат."""
    total = 0
    for i in range(start, end):
        total += i
    return total


def main():
    chunk = TOTAL // NUM_PROCESSES
    ranges = []
    for i in range(NUM_PROCESSES):
        s = i * chunk + 1
        e = (i + 1) * chunk + 1 if i < NUM_PROCESSES - 1 else TOTAL + 1
        ranges.append((s, e))

    start_time = time.perf_counter()

    with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
        results = pool.starmap(calculate_sum, ranges)

    total_sum = sum(results)
    elapsed = time.perf_counter() - start_time

    expected = TOTAL * (TOTAL + 1) // 2
    print(f"[multiprocessing] Сумма:    {total_sum}")
    print(f"[multiprocessing] Ожидалось:{expected}")
    print(f"[multiprocessing] Совпадает: {total_sum == expected}")
    print(f"[multiprocessing] Время:    {elapsed:.4f} сек")


if __name__ == "__main__":
    main()
