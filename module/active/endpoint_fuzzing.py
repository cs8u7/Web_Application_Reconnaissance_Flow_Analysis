import requests
from concurrent.futures import ThreadPoolExecutor

endpoint_count = 0

def fuzz(target_url, endpoint_fuzzing_sample, endpoint_range):
    global endpoint_count
    endpoint_count += 1
    print(f"[{(endpoint_count / endpoint_range) * 100:.2f}%][{endpoint_count}/{endpoint_range}]", end='\r')
    try:
        response = requests.get(target_url, timeout=2)

        with open(endpoint_fuzzing_sample, 'a') as file:
            file.write(f'[{response.status_code}] {target_url}\n')
    except requests.RequestException:
        pass


def multi_threads_fuzzing(target_url, threads, endpoint_fuzzing_sample):
    with open('module/active/word_list/endpoint.txt', 'r') as file:
        payloads = file.read().splitlines()
    endpoint_range = len(payloads)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(fuzz, target_url.format(
            payload), endpoint_fuzzing_sample, endpoint_range) for payload in payloads]

        for future in futures:
            try:
                future.result()
            except Exception:
                pass


def endpoint_fuzzing(domain, threads, folder_result):
    endpoint_fuzzing_sample = folder_result + f'/active/endpoint_fuzzing.txt'
    target_url = 'https://' + domain + "/{}"
    multi_threads_fuzzing(target_url, threads, endpoint_fuzzing_sample)