import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL = "https://cs2-tracked.onrender.com"
TOTAL_REQUESTS = 200
CONCURRENT_USERS = 20

def send_request(_):
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(URL, timeout=10) as response:
            status = response.status
            response.read()
        return (time.perf_counter() - t0) * 1000, status == 200
    except Exception:
        return (time.perf_counter() - t0) * 1000, False

def run_load_test():
    print(f"Pornire Load Test pe {URL}: {TOTAL_REQUESTS} cereri cu {CONCURRENT_USERS} utilizatori simultani...")
    start_total = time.perf_counter()

    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        results = list(executor.map(send_request, range(TOTAL_REQUESTS)))

    total_time_s = time.perf_counter() - start_total
    latencies = [r[0] for r in results]
    successes = sum(1 for r in results if r[1])

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    rps = TOTAL_REQUESTS / total_time_s

    print("\n================ REZULTATE LOAD TEST ================")
    print(f"Cereri totale trimise : {TOTAL_REQUESTS}")
    print(f"Cereri reusite (200)  : {successes}/{TOTAL_REQUESTS}")
    print(f"Timp total executie   : {total_time_s:.2f} secunde")
    print(f"Requests Per Second   : {rps:.2f} req/s")
    print(f"Timp raspuns mediu    : {avg_latency:.2f} ms")
    print(f"Timp raspuns minim    : {min_latency:.2f} ms")
    print(f"Timp raspuns maxim    : {max_latency:.2f} ms")
    print("=====================================================")

if __name__ == "__main__":
    run_load_test()