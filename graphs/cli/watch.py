"""Hot-reload renderer for ``graphs/`` + ``examples/``.

Watches Python files under ``graphs/`` and ``examples/`` and re-renders the
affected example scripts + comparison strips on change.

Dispatch rules:
    graphs/**.py                  -> regen ALL examples + comparisons
    examples/_data.py             -> regen ALL examples + comparisons
    examples/build_comparisons.py -> rebuild comparisons only
    examples/<name>.py            -> regen that one + comparisons

Exposed via ``[project.scripts]`` as ``graphs-watch``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

# Line-buffer stdout so `graphs-watch | tee log` and `> log` show progress
# in real time rather than only on process exit.
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

REPO = Path(__file__).resolve().parents[2]
EXAMPLES = REPO / "examples"

DEBOUNCE_SECONDS = 0.4
SKIP_STEMS = {"_data", "build_comparisons", "__init__"}


def _run(cmd: list[str]) -> tuple[int, str]:
    """Run ``cmd`` in the repo root, returning (exit_code, combined_output)."""
    res = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
    return res.returncode, (res.stdout or "") + (res.stderr or "")


def _print_tail(output: str, lines: int = 20) -> None:
    tail = output.strip().splitlines()[-lines:]
    for line in tail:
        sys.stderr.write(f"    {line}\n")


def _render_example(path: Path) -> bool:
    rc, out = _run(["uv", "run", "--with", "scipy", "python", str(path)])
    ok = rc == 0
    marker = "ok" if ok else "FAIL"
    print(f"  [{marker}] {path.name}")
    if not ok:
        _print_tail(out)
    return ok


def rebuild_comparisons() -> bool:
    print("- comparisons")
    rc, out = _run(
        [
            "uv",
            "run",
            "--with",
            "pillow",
            "--with",
            "requests",
            "python",
            str(EXAMPLES / "build_comparisons.py"),
        ]
    )
    ok = rc == 0
    marker = "ok" if ok else "FAIL"
    print(f"  [{marker}] build_comparisons.py")
    if not ok:
        _print_tail(out)
    return ok


def _iter_examples() -> list[Path]:
    return sorted(
        p
        for p in EXAMPLES.glob("*.py")
        if p.stem not in SKIP_STEMS and not p.stem.startswith("_")
    )


def regen_all() -> None:
    examples = _iter_examples()
    workers = min(len(examples), os.cpu_count() or 4)
    print(f"- regen all examples ({len(examples)}, {workers} workers)")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        # list() blocks until all renders complete; _render_example prints its
        # own [ok]/[FAIL] line so the interleaved output is still readable.
        list(pool.map(_render_example, examples))
    rebuild_comparisons()


def regen_one(example_path: Path) -> None:
    print(f"- {example_path.name}")
    _render_example(example_path)
    rebuild_comparisons()


class _Handler(FileSystemEventHandler):
    """Debounced collector of .py change events."""

    def __init__(self) -> None:
        self._pending: dict[Path, float] = {}
        self._lock = threading.Lock()

    def _note(self, src: str) -> None:
        path = Path(src)
        if path.suffix != ".py":
            return
        if "__pycache__" in path.parts or ".venv" in path.parts:
            return
        with self._lock:
            self._pending[path] = time.monotonic()

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._note(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._note(event.src_path)

    def drain(self) -> list[Path]:
        now = time.monotonic()
        with self._lock:
            ready = [p for p, t in self._pending.items() if now - t >= DEBOUNCE_SECONDS]
            for p in ready:
                del self._pending[p]
        return ready


def dispatch(path: Path) -> None:
    try:
        rel = path.resolve().relative_to(REPO)
    except ValueError:
        return
    parts = rel.parts
    if not parts:
        return
    if parts[0] == "graphs":
        print(f"~ helper change: {rel}")
        regen_all()
        return
    if parts[0] != "examples" or len(parts) != 2:
        return
    name = parts[1]
    if name == "_data.py":
        print(f"~ data change: {rel}")
        regen_all()
    elif name == "build_comparisons.py":
        print("~ comparison builder change")
        rebuild_comparisons()
    elif name.endswith(".py") and not name.startswith("_"):
        print(f"~ example change: {rel}")
        regen_one(path)


def main() -> int:
    regen_all()

    handler = _Handler()
    observer = Observer()
    observer.schedule(handler, str(REPO / "graphs"), recursive=True)
    observer.schedule(handler, str(EXAMPLES), recursive=False)
    observer.start()

    print("watching graphs/ and examples/ for .py changes (Ctrl-C to stop)")
    try:
        while True:
            time.sleep(DEBOUNCE_SECONDS)
            seen: set[Path] = set()
            for path in handler.drain():
                if path in seen:
                    continue
                seen.add(path)
                dispatch(path)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
