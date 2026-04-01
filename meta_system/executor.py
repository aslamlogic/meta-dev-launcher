from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, List, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class Executor:
    def run_parallel(self, items: Iterable[T], fn: Callable[[T], R], max_workers: int | None = None) -> List[R]:
        items = list(items)
        if not items:
            return []
        results: List[R] = [None] * len(items)  # type: ignore[list-item]
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_map = {pool.submit(fn, item): idx for idx, item in enumerate(items)}
            for future in as_completed(future_map):
                idx = future_map[future]
                results[idx] = future.result()
        return results
