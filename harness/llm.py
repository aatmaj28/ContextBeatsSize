"""Anthropic + Groq calls with retries, cost accounting and a budget guard."""
import os
import random
import threading
import time
from dataclasses import dataclass

from .config import (API_MAX_RETRIES, HAIKU_PRICE_TIER_LIMIT, MAX_TOKENS, PROMPT_TOKEN_ASSERT, Model, cost_usd,
                     worst_case_cost)


class BudgetExceeded(Exception):
    pass


class Budget:
    """Thread-safe spend tracker. Each call reserves its worst-case cost first, so concurrent
    calls can never push the total over the limit."""

    def __init__(self, limit_usd: float, spent_usd: float = 0.0):
        self.limit = limit_usd
        self.spent = spent_usd
        self.reserved = 0.0
        self._lock = threading.Lock()

    def reserve(self, amount: float) -> None:
        with self._lock:
            if self.spent + self.reserved + amount > self.limit:
                raise BudgetExceeded(
                    f"next call could cost up to ${amount:.4f}; spent ${self.spent:.4f} "
                    f"+ in flight ${self.reserved:.4f} would exceed MAX_SPEND_USD=${self.limit:.2f}")
            self.reserved += amount

    def settle(self, reserved: float, actual: float) -> None:
        with self._lock:
            self.reserved -= reserved
            self.spent += actual


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    api_latency_s: float
    stop_reason: str
    api_retries: int


_clients = {}
_clients_lock = threading.Lock()


def _client(provider: str):
    with _clients_lock:
        if provider not in _clients:
            if provider == "anthropic":
                import anthropic
                # Keys not scoped to a workspace must name one on every request.
                workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID")
                headers = {"anthropic-workspace-id": workspace} if workspace else None
                _clients[provider] = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], max_retries=0,
                                                         default_headers=headers)
            else:
                import groq
                _clients[provider] = groq.Groq(api_key=os.environ["GROQ_API_KEY"], max_retries=0)
        return _clients[provider]


def _retryable(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status is not None:
        return status in (408, 409, 429) or status >= 500  # 529 = overloaded
    name = type(exc).__name__
    return name in ("APIConnectionError", "APITimeoutError")


def _retry_after(exc: Exception):
    try:
        return float(exc.response.headers.get("retry-after"))
    except Exception:
        return None


def _call_anthropic(model: Model, system: str, user: str):
    resp = _client("anthropic").messages.create(
        model=model.model_id,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    # Opus 5.5 always thinks; only text blocks carry the answer.
    text = "".join(b.text for b in resp.content if b.type == "text")
    return text, resp.usage.input_tokens, resp.usage.output_tokens, resp.stop_reason


def _call_groq(model: Model, system: str, user: str):
    resp = _client("groq").chat.completions.create(
        model=model.model_id,
        max_completion_tokens=MAX_TOKENS,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    choice = resp.choices[0]
    stop = {"length": "max_tokens", "stop": "end_turn"}.get(choice.finish_reason, choice.finish_reason)
    return choice.message.content or "", resp.usage.prompt_tokens, resp.usage.completion_tokens, stop


def call_model(model: Model, system: str, user: str, budget: Budget) -> LLMResponse:
    prompt_chars = len(system) + len(user)
    assert prompt_chars / 3 < PROMPT_TOKEN_ASSERT, f"prompt too large (~{prompt_chars / 3:.0f} tokens)"
    reserve = worst_case_cost(model, prompt_chars)
    budget.reserve(reserve)
    actual = 0.0
    try:
        call = _call_anthropic if model.provider == "anthropic" else _call_groq
        for retry in range(API_MAX_RETRIES + 1):
            t0 = time.monotonic()
            try:
                text, tin, tout, stop = call(model, system, user)
            except Exception as exc:
                if not _retryable(exc) or retry == API_MAX_RETRIES:
                    raise
                wait = _retry_after(exc) or min(60.0, 2.0 * 2 ** retry) + random.uniform(0, 1)
                print(f"    api retry {retry + 1}/{API_MAX_RETRIES} for {model.model_id} after "
                      f"{type(exc).__name__} ({getattr(exc, 'status_code', '-')}); sleeping {wait:.1f}s", flush=True)
                time.sleep(wait)
                continue
            latency = time.monotonic() - t0  # only the successful request counts
            actual = cost_usd(model, tin, tout)
            assert tin < HAIKU_PRICE_TIER_LIMIT, f"prompt used {tin} input tokens; price tier assumption broken"
            return LLMResponse(text, tin, tout, actual, round(latency, 3), stop or "unknown", retry)
    finally:
        budget.settle(reserve, actual)
