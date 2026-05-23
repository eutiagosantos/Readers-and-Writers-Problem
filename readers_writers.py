#!/usr/bin/env python3
"""Problema dos Leitores e Escritores — vetor M partilhado com threads e semáforos."""

import threading
import time

M = [3, 7, 1, 9]
read_count = 0
mutex = threading.Semaphore(1)
rw = threading.Semaphore(1)
_log_lock = threading.Lock()


def _log(msg: str) -> None:
    with _log_lock:
        print(f"[{time.time():.3f}] {msg}", flush=True)


def reader(reader_id: str, op: str) -> None:
    global read_count

    mutex.acquire()
    read_count += 1
    if read_count == 1:
        rw.acquire()
    mutex.release()

    _log(f"{reader_id} → entrou (leitura)")
    time.sleep(0.08)

    if op == "index_3":
        value = M[3]
        _log(f"{reader_id}: M[3] = {value}")
    elif op == "full":
        snapshot = list(M)
        _log(f"{reader_id}: M = {snapshot}")
    elif op == "index_1":
        value = M[1]
        _log(f"{reader_id}: M[1] = {value}")

    _log(f"{reader_id} ← saiu (leitura)")

    mutex.acquire()
    read_count -= 1
    if read_count == 0:
        rw.release()
    mutex.release()


def writer(writer_id: str, op: str) -> None:
    rw.acquire()

    _log(f"{writer_id} → entrou (escrita)")
    time.sleep(0.08)

    if op == "set_index_3":
        M[3] = 2
        _log(f"{writer_id}: M[3] = 2  →  M = {list(M)}")
    elif op == "set_all":
        new_values = [2, 1, 0, 6]
        for i, v in enumerate(new_values):
            M[i] = v
        _log(f"{writer_id}: M = {new_values}")

    _log(f"{writer_id} ← saiu (escrita)")
    rw.release()


def main() -> None:
    _log(f"Estado inicial: M = {list(M)}")

    threads = [
        threading.Thread(target=writer, args=("e1", "set_index_3"), name="e1"),
        threading.Thread(target=writer, args=("e2", "set_all"), name="e2"),
        threading.Thread(target=reader, args=("l1", "index_3"), name="l1"),
        threading.Thread(target=reader, args=("l2", "full"), name="l2"),
        threading.Thread(target=reader, args=("l3", "index_1"), name="l3"),
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    _log(f"Estado final: M = {list(M)}")


if __name__ == "__main__":
    main()
