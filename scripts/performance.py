"""Predefined ordinary/peak read journeys against a live controlled API."""
import argparse
import asyncio
import math
import os
import time

import httpx
import psutil

from backend.app.config import Settings
from scripts.metadata import metadata, write_json


async def model(base, concurrency, think, duration, pid):
    clients = [httpx.AsyncClient(base_url=base, timeout=12) for _ in range(concurrency)]
    for client in clients:
        response = await client.post('/api/auth/login', json={'username': 'teacher', 'password': os.environ['DEMO_TEACHER_PASSWORD']})
        response.raise_for_status()
    times, errors, samples = [], [], []
    process = psutil.Process(pid) if pid else None
    if process: process.cpu_percent()
    async def user(client, index, until, collect):
        counter = index
        while time.monotonic() < until:
            route = '/api/dashboard' if counter % 10 < 5 else '/api/sessions' if counter % 10 < 8 else '/api/reports'
            started = time.perf_counter()
            try:
                result = await client.get(route)
                status = result.status_code
            except httpx.HTTPError:
                status = 0
            if collect:
                times.append((time.perf_counter()-started)*1000)
                if status != 200: errors.append(status)
            counter += 1
            await asyncio.sleep(think)
    async def resources(until):
        while time.monotonic() < until:
            if process:
                samples.append({'elapsed_seconds': round(duration-(until-time.monotonic()), 3), 'cpu_percent': process.cpu_percent(), 'rss_bytes': process.memory_info().rss})
            await asyncio.sleep(.25)
    try:
        warm_until = time.monotonic()+3
        await asyncio.gather(*(user(client, index, warm_until, False) for index, client in enumerate(clients)))
        start = time.monotonic(); until = start+duration
        await asyncio.gather(*(user(client, index, until, True) for index, client in enumerate(clients)), resources(until))
        elapsed = time.monotonic()-start
    finally:
        for client in clients: await client.aclose()
    ordered = sorted(times)
    def percentile(value): return round(ordered[max(0, math.ceil(value*len(ordered))-1)], 3) if ordered else None
    return {'concurrency': concurrency, 'think_seconds': think, 'warmup_seconds': 3, 'measurement_target_seconds': duration, 'elapsed_seconds': round(elapsed, 3), 'requests': len(times), 'p50_ms': percentile(.5), 'p95_ms': percentile(.95), 'p99_ms': percentile(.99), 'throughput_requests_per_second': round(len(times)/elapsed, 3), 'unexpected_errors': len(errors), 'unexpected_error_rate': len(errors)/len(times) if times else 1, 'error_statuses': errors, 'resource_samples': samples, 'latencies_ms': [round(x, 3) for x in times], 'percentile_method': 'nearest rank'}


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:8000')
    parser.add_argument('--pid', type=int)
    args = parser.parse_args()
    Settings.from_env()
    results = []
    for name, users, think in [('ordinary', 3, .20), ('peak', 12, .05)]:
        result = await model(args.base, users, think, 20, args.pid)
        result['name'] = name
        result['candidate_thresholds'] = {'p95_ms_below': 750, 'unexpected_error_rate_below': .01}
        result['threshold_met'] = result['p95_ms'] is not None and result['p95_ms'] < 750 and result['unexpected_error_rate'] < .01
        results.append(result)
        print(f'{name}: {result["requests"]} requests, p95={result["p95_ms"]}ms, errors={result["unexpected_errors"]}')
    write_json('evidence/week16/performance.json', {'metadata': metadata('python -m scripts.performance --pid <owned API PID>', '1 class, 12 fictional learners, 1 session; shared teacher role with independent sessions'), 'request_mix': {'dashboard': .5, 'sessions': .3, 'reports': .2}, 'scope': 'Local read-heavy short-run evaluation, not stress/endurance or distributed production proof', 'results': results})


if __name__ == '__main__': asyncio.run(main())
