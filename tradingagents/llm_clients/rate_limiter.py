"""Client-side tokens-per-minute pacing for providers with tight free-tier caps.

Groq's free tier caps every current model (openai/gpt-oss-120b,
openai/gpt-oss-20b, qwen/qwen3.6-27b) at 8000 TPM. Exceeding it returns an
HTTP 413/429 with code "rate_limit_exceeded" — the openai SDK's built-in
retry logic doesn't retry 413s and only retries 429s a couple of times with
short backoff, so a single burst of analyst calls reliably crashes the run.

This module tracks token usage in a rolling 60s window per model and makes
callers wait before a request would push the window over budget, plus
retries the provider's own rate-limit response with the wait time it
suggests instead of surfacing a raw traceback.
"""

from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from typing import Any, Optional

# Groq free tier: 8000 TPM on every current model. Leave headroom below the
# hard cap so estimation error (chars/4 is approximate) doesn't itself
# trigger the provider's own limit.
DEFAULT_TPM_LIMIT = 8000
SAFETY_MARGIN = 0.9  # use at most 90% of the cap when pacing proactively

_RETRY_AFTER_RE = re.compile(r"try again in ([\d.]+)s", re.IGNORECASE)


def estimate_tokens(input_: Any, tools: Optional[list] = None) -> int:
    """Rough token estimate (~4 chars/token) for pacing, not billing.

    Good enough to decide whether a request is likely to fit the remaining
    per-minute budget; the window is corrected with the provider's actual
    reported usage after each call via ``record_actual``.
    """
    text_len = 0
    messages = input_
    if hasattr(messages, "to_messages"):
        messages = messages.to_messages()
    if isinstance(messages, list):
        for m in messages:
            content = getattr(m, "content", m)
            if isinstance(content, str):
                text_len += len(content)
            else:
                text_len += len(str(content))
    else:
        text_len += len(str(messages))

    if tools:
        try:
            text_len += len(json.dumps(tools))
        except (TypeError, ValueError):
            text_len += sum(len(str(t)) for t in tools)

    return max(1, text_len // 4)


class TokenPerMinuteLimiter:
    """Sliding-window limiter: waits so a rolling 60s window stays under budget."""

    def __init__(self, tpm_limit: int = DEFAULT_TPM_LIMIT):
        self.tpm_limit = tpm_limit
        self._window: deque[tuple[float, int]] = deque()
        self._lock = threading.Lock()

    def _prune(self, now: float) -> int:
        cutoff = now - 60
        while self._window and self._window[0][0] < cutoff:
            self._window.popleft()
        return sum(tokens for _, tokens in self._window)

    def reserve(self, estimated_tokens: int) -> None:
        """Block until ``estimated_tokens`` fits in the rolling budget, then reserve it."""
        budget = int(self.tpm_limit * SAFETY_MARGIN)
        with self._lock:
            while True:
                now = time.monotonic()
                used = self._prune(now)
                if used + estimated_tokens <= budget or not self._window:
                    self._window.append((now, estimated_tokens))
                    return
                # Wait until the oldest entry ages out of the 60s window.
                wait_for = self._window[0][0] + 60 - now
                if wait_for > 0:
                    time.sleep(min(wait_for, 5))

    def record_actual(self, estimated_tokens: int, actual_tokens: int) -> None:
        """Replace the most recent reservation with the provider-reported count."""
        if actual_tokens <= 0:
            return
        with self._lock:
            for i in range(len(self._window) - 1, -1, -1):
                ts, tokens = self._window[i]
                if tokens == estimated_tokens:
                    self._window[i] = (ts, actual_tokens)
                    return


_limiters: dict[str, TokenPerMinuteLimiter] = {}
_limiters_lock = threading.Lock()


def get_limiter(model: str, tpm_limit: int = DEFAULT_TPM_LIMIT) -> TokenPerMinuteLimiter:
    with _limiters_lock:
        limiter = _limiters.get(model)
        if limiter is None:
            limiter = TokenPerMinuteLimiter(tpm_limit)
            _limiters[model] = limiter
        return limiter


def parse_retry_after_seconds(error: Exception, default: float = 20.0) -> float:
    """Best-effort wait time from a Groq rate-limit error.

    Prefers the HTTP ``retry-after`` header; falls back to the "try again
    in N.NNs" text Groq embeds in the error message.
    """
    response = getattr(error, "response", None)
    header = getattr(response, "headers", {}).get("retry-after") if response is not None else None
    if header:
        try:
            return float(header)
        except (TypeError, ValueError):
            pass
    match = _RETRY_AFTER_RE.search(str(error))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return default


def is_tpm_rate_limit_error(error: Exception) -> bool:
    status_code = getattr(error, "status_code", None)
    return status_code in (413, 429) and "rate_limit_exceeded" in str(error)
