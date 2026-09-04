"""LLM client: caching, rate limiting, retries, metering, budget fail-safe
(ENGINEERING.md guarantees 3-5).

Every call flows: budget check -> cache lookup -> rate limiter -> HTTP with
retry/backoff -> meter -> cache store. Replay mode skips the network entirely
and raises on a cache miss, which is what makes every published number
recomputable without an API key.
"""

import hashlib
import json
import os
import random
import sqlite3
import threading
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]


class BudgetStop(RuntimeError):
    """Raised when a call would cross a spend ceiling. The run pauses itself."""


def load_env_key(*names):
    """Read an API key from the environment or the gitignored .env file.
    Accepts multiple names (e.g. OPENROUTER_TOKEN and OPENROUTER_KEY)."""
    for name in names:
        if os.environ.get(name):
            return os.environ[name]
    env = REPO_ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            for name in names:
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip()
    return None


class RateLimiter:
    """Token buckets for requests/min and tokens/min, per provider.
    acquire() blocks until sending is polite. Thread-safe."""

    def __init__(self, rpm, tpm):
        self.rpm, self.tpm = rpm, tpm
        self._lock = threading.Lock()
        self._req_allow = float(rpm)
        self._tok_allow = float(tpm)
        self._last = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        dt = now - self._last
        self._last = now
        self._req_allow = min(self.rpm, self._req_allow + dt * self.rpm / 60.0)
        self._tok_allow = min(self.tpm, self._tok_allow + dt * self.tpm / 60.0)

    def acquire(self, est_tokens):
        while True:
            with self._lock:
                self._refill()
                if self._req_allow >= 1 and self._tok_allow >= est_tokens:
                    self._req_allow -= 1
                    self._tok_allow -= est_tokens
                    return
                need_req = max(0.0, (1 - self._req_allow) * 60.0 / self.rpm)
                need_tok = max(0.0, (est_tokens - self._tok_allow) * 60.0 / self.tpm)
            time.sleep(min(max(need_req, need_tok, 0.05), 10.0))

    def punish(self):
        """Called after a 429: empty the buckets so we back off collectively."""
        with self._lock:
            self._req_allow = 0.0
            self._tok_allow = 0.0


class LLMCache:
    """SQLite response cache keyed by the full canonical request."""

    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, ts REAL)")
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, key, value):
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
                (key, json.dumps(value, ensure_ascii=False), time.time()))
            self._conn.commit()


class Meter:
    """Append-only tokens.log: every call metered before its result is used."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(self, entry):
        with self._lock, open(self.path, "a") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            fh.flush()

    def total_cost(self):
        if not self.path.exists():
            return 0.0
        total = 0.0
        with open(self.path) as fh:
            for line in fh:
                try:
                    total += json.loads(line).get("est_cost", 0.0)
                except json.JSONDecodeError:
                    continue
        return total


class LLMClient:
    """One client per (provider, model, role). See providers in config.json."""

    RETRIABLE = {429, 500, 502, 503, 504}

    def __init__(self, *, name, base_url, key_names, model, price_in_per_m,
                 price_out_per_m, rpm, tpm, meter, cache,
                 provider_pin=None, budget_ceiling=None, mode="live",
                 max_retries=12, transport=None):
        self.name, self.base_url, self.model = name, base_url, model
        self.api_key = load_env_key(*key_names) if key_names else None
        self.price_in, self.price_out = price_in_per_m, price_out_per_m
        self.limiter = RateLimiter(rpm, tpm)
        self.meter, self.cache = meter, cache
        self.provider_pin = provider_pin
        self.budget_ceiling = budget_ceiling
        self.mode = mode
        self.max_retries = max_retries
        self._transport = transport or self._http_post  # injectable for tests

    # ---- the one public method ---------------------------------------------

    def chat(self, messages, *, temperature=0.7, max_tokens=1200, tag=""):
        body = {"model": self.model, "messages": messages,
                "temperature": temperature, "max_tokens": max_tokens}
        if self.provider_pin:
            body["provider"] = {"order": [self.provider_pin],
                                 "allow_fallbacks": False}
        key = hashlib.sha256(
            json.dumps([self.name, body], sort_keys=True,
                       ensure_ascii=False).encode()).hexdigest()

        cached = self.cache.get(key)
        if cached is not None:
            return cached["text"]
        if self.mode == "replay":
            raise KeyError(f"replay mode cache miss for tag={tag}")

        self._budget_check()
        est_tokens = sum(len(m.get("content", "")) for m in messages) // 3 + max_tokens
        self.limiter.acquire(est_tokens)
        t0 = time.monotonic()
        resp = self._request_with_retries(body)
        latency_ms = int((time.monotonic() - t0) * 1000)

        usage = resp.get("usage", {})
        tin = usage.get("prompt_tokens", est_tokens)
        tout = usage.get("completion_tokens", 0)
        # Prefer the provider's own reported cost (OpenRouter returns it);
        # fall back to our price-table estimate.
        cost = usage.get("cost")
        if cost is None:
            cost = tin / 1e6 * self.price_in + tout / 1e6 * self.price_out
        self.meter.record({"ts": time.time(), "client": self.name,
                           "model": self.model, "tag": tag,
                           "in_tokens": tin, "out_tokens": tout,
                           "est_cost": round(cost, 6),
                           "latency_ms": latency_ms})

        text = resp["choices"][0]["message"].get("content")
        if not text or not text.strip():
            # An empty completion is a provider hiccup, not an answer:
            # never cache it, surface it as a retriable failure.
            raise RuntimeError(f"{self.name}: empty completion (tag={tag})")
        self.cache.put(key, {"text": text, "usage": usage})
        return text

    # ---- internals ----------------------------------------------------------

    def _budget_check(self):
        if self.budget_ceiling is not None:
            spent = self.meter.total_cost()
            if spent >= self.budget_ceiling:
                raise BudgetStop(
                    f"spent ${spent:.2f} >= ceiling ${self.budget_ceiling:.2f}")

    def _request_with_retries(self, body):
        last_err = None
        for attempt in range(self.max_retries + 1):
            # transport-level failures (connection reset, SSL, timeout)
            # are retriable exactly like a 503 — arm B of the pilot died
            # to an uncaught ConnectionError under concurrent load.
            terr = None
            try:
                status, payload, retry_after = self._transport(body)
            except Exception as e:
                status, payload, retry_after = 503, {}, None
                terr = f"transport: {type(e).__name__}: {str(e)[:80]}"
            if status == 200:
                # OpenRouter can return 200 with an error object instead
                # of a completion (provider failure surfaced in-band) —
                # retriable like any transient failure, never a KeyError.
                if "choices" in payload and payload["choices"]:
                    return payload
                status = 503  # fall through to the retriable path
                last_err = f"200-without-choices: {str(payload)[:120]}"
            else:
                last_err = terr or f"HTTP {status}"
            if status not in self.RETRIABLE or attempt == self.max_retries:
                raise RuntimeError(
                    f"{self.name}: {last_err} after {attempt + 1} attempts"
                    f" | body: {str(payload)[:300]}")
            if status == 429:
                self.limiter.punish()
            # 429 means "wait", not "fail": a resumable overnight run
            # should outlast sustained throttling (arm A died to seven
            # straight 429s under 3-process load). Non-429s keep the
            # short cap.
            cap = 300.0 if status == 429 else 60.0
            wait = retry_after or min(cap, (2 ** attempt) + random.random())
            time.sleep(wait)
        raise RuntimeError(f"{self.name}: exhausted retries ({last_err})")

    def _http_post(self, body):
        r = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            json=body, timeout=180)
        retry_after = None
        if "Retry-After" in r.headers:
            try:
                retry_after = float(r.headers["Retry-After"])
            except ValueError:
                pass
        try:
            payload = r.json()
        except ValueError:
            payload = {}
        return r.status_code, payload, retry_after
