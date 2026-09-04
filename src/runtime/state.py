"""Run state: the crash-safety, resume, and safe-pause layer (ENGINEERING.md guarantees 1-2).

Design in one breath: the only source of truth is an append-only events.jsonl
per run. Completing an atomic step appends one line; nothing is ever rewritten.
Resume = re-read the log, skip what's done. Pause = a PAUSE file or Ctrl-C,
both of which finish the current step and exit cleanly. Snapshots are written
atomically (temp file -> fsync -> rename), so a crash can never leave a
half-written file that a resume would trust.
"""

import json
import os
import signal
import tempfile
import time
from pathlib import Path


class RunState:
    """Owns one run directory: its event log, status, pause and stop signals."""

    def __init__(self, run_dir, control_dir=None):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.control_dir = Path(control_dir) if control_dir else None
        self.events_path = self.run_dir / "events.jsonl"
        self._stop_requested = False
        self._done_steps = set()
        self._load()

    # ---- resume -------------------------------------------------------------

    def _load(self):
        """Replay the event log so `is_done` answers instantly."""
        if not self.events_path.exists():
            return
        with open(self.events_path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    # A torn final line from a crash mid-append: ignore it.
                    # The step it described never completed and will be redone.
                    continue
                if "step" in ev:
                    self._done_steps.add(ev["step"])

    def is_done(self, step_id):
        return step_id in self._done_steps

    def forget(self, step_id):
        """Remove a step from the done-set for THIS process only — the log
        keeps its history; the step will re-run and append a fresh event.
        For retry semantics: callers forget failed steps at startup."""
        self._done_steps.discard(step_id)

    # ---- recording ----------------------------------------------------------

    def record(self, step_id, event_type, payload=None):
        """Mark an atomic step complete. Append-only, flushed to disk."""
        ev = {"ts": time.time(), "step": step_id, "type": event_type}
        if payload is not None:
            ev["data"] = payload
        with open(self.events_path, "a") as fh:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self._done_steps.add(step_id)

    @staticmethod
    def atomic_write_json(path, obj):
        """Snapshot writes that a crash cannot tear: temp -> fsync -> rename."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_")
        try:
            with os.fdopen(fd, "w") as fh:
                json.dump(obj, fh, ensure_ascii=False, indent=2)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # ---- pause / stop -------------------------------------------------------

    def install_signal_handlers(self):
        """Ctrl-C / SIGTERM = 'finish the current step, then exit cleanly'."""
        def _handler(signum, frame):
            self._stop_requested = True
        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)

    def pause_requested(self):
        if (self.run_dir / "PAUSE").exists():
            return True
        if self.control_dir and (self.control_dir / "PAUSE").exists():
            return True
        return False

    def should_stop(self):
        """Checked between atomic steps — the only places stopping happens."""
        return self._stop_requested or self.pause_requested()

    def set_status(self, status, detail=None):
        self.atomic_write_json(self.run_dir / "status.json", {
            "status": status, "detail": detail, "ts": time.time(),
        })
