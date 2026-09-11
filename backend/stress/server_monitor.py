"""压测期间后台采样后端进程 CPU/内存，输出 CSV，用于判断事件循环是否被阻塞。

运行（与压测同时，另开一个终端）：
    venv\\Scripts\\python stress/server_monitor.py --pid <后端进程PID> --out results/server.csv

说明：
  - Windows 上无 num_fds，改采 num_handles（句柄数）。
  - 若 CPU 长时间打满单核，且聊天 ttft 同步飙升，说明同步检索阻塞了事件循环。
"""
import argparse
import csv
import time

import psutil


def _handle_count(proc):
    for attr in ("num_handles", "num_fds"):
        fn = getattr(proc, attr, None)
        if fn is not None:
            try:
                return fn()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                return -1
    return -1


def main(pid: int, interval: float, out: str, duration: float | None) -> None:
    proc = psutil.Process(pid)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ts_s", "cpu_percent", "rss_mb", "num_threads", "num_handles"])
        t0 = time.time()
        while True:
            if duration is not None and (time.time() - t0) >= duration:
                break
            try:
                # cpu_percent(interval) 会阻塞 interval 秒并返回期间平均占用
                cpu = proc.cpu_percent(interval=interval)
                mem = proc.memory_info().rss / 1024 / 1024
                threads = proc.num_threads()
                handles = _handle_count(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            w.writerow([f"{time.time() - t0:.1f}", f"{cpu:.1f}", f"{mem:.1f}",
                        threads, handles])
            f.flush()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="后端进程资源采样")
    p.add_argument("--pid", type=int, required=True, help="后端 python 进程 PID")
    p.add_argument("--interval", type=float, default=1.0, help="采样间隔（秒）")
    p.add_argument("--out", type=str, default="results/server.csv", help="输出 CSV 路径")
    p.add_argument("--duration", type=float, default=None, help="采样时长（秒），默认无限")
    a = p.parse_args()
    main(a.pid, a.interval, a.out, a.duration)
