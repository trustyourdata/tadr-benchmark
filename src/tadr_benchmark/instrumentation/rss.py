"""Sample absolute worker-tree RSS, excluding the supervisor by construction."""

import time

import psutil


class RssMonitor:
    def __init__(self, worker_pid: int, process_factory=psutil.Process):
        self.peak = None
        self.baseline = None
        self.successful_samples = 0
        self.largest_gap = None
        self.last_sample = None
        self.discovery_failed = False
        self.incomplete = False
        self.vanished = 0
        try:
            self.root = process_factory(worker_pid)
        except (psutil.Error, OSError):
            self.root = None
            self.incomplete = True

    def sample(self) -> int | None:
        if self.root is None:
            return None
        now = time.perf_counter_ns()
        try:
            children = self.root.children(recursive=True)
        except (psutil.Error, OSError):
            self.discovery_failed = self.incomplete = True
            return None
        try:
            total = self.root.memory_info().rss
        except (psutil.Error, OSError):
            self.incomplete = True
            return None
        seen = {self.root.pid}
        for child in children:
            if child.pid in seen:
                continue
            seen.add(child.pid)
            try:
                total += child.memory_info().rss
            except psutil.NoSuchProcess:
                self.vanished += 1
            except (psutil.Error, OSError):
                self.incomplete = True
                return None
        if self.last_sample is not None:
            gap = (now-self.last_sample)/1e9
            self.largest_gap = max(self.largest_gap or 0.0, gap)
        self.last_sample = now
        self.successful_samples += 1
        self.peak = max(self.peak or 0, total)
        if self.baseline is None:
            self.baseline = total
        return total
