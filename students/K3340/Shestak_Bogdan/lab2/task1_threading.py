import threading
import time

TOTAL = 10_000_000_000  # 10^10
NUM_THREADS = 8


def calculate_sum(start: int, end: int, results: list, index: int) -> None:
    """Считает сумму чисел в диапазоне [start, end) и сохраняет в results[index]."""
    total = 0
    for i in range(start, end):
        total += i
    results[index] = total


def main():
    chunk = TOTAL // NUM_THREADS
    threads = []
    results = [0] * NUM_THREADS

    start_time = time.perf_counter()

    for i in range(NUM_THREADS):
        s = i * chunk + 1
        e = (i + 1) * chunk + 1 if i < NUM_THREADS - 1 else TOTAL + 1
        t = threading.Thread(target=calculate_sum, args=(s, e, results, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    total_sum = sum(results)
    elapsed = time.perf_counter() - start_time

    expected = TOTAL * (TOTAL + 1) // 2
    print(f"[threading] Сумма:    {total_sum}")
    print(f"[threading] Ожидалось:{expected}")
    print(f"[threading] Совпадает: {total_sum == expected}")
    print(f"[threading] Время:    {elapsed:.4f} сек")


if __name__ == "__main__":
    main()
