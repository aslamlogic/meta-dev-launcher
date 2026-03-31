from concurrent.futures import ThreadPoolExecutor, as_completed


class Executor:
    def run_parallel(self, tasks):
        results = []
        if not tasks:
            return results

        with ThreadPoolExecutor(max_workers=min(32, len(tasks))) as pool:
            futures = [pool.submit(task) for task in tasks]
            for future in as_completed(futures):
                results.append(future.result())
        return results
