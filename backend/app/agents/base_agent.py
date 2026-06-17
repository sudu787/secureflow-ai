"""
SecureFlow AI - Base Agent (Multi-LLM) — Optimized
Abstract base class for all specialized AI agents.
Supports multiple LLM providers: Gemini (Google) and Grok (xAI).

Efficiency features:
  - Response cache (LRU) to avoid duplicate LLM calls
  - Circuit breaker per provider (stops calling after repeated failures)
  - Adaptive token limits per agent type
  - Single-retry with fast fallback (no wasted retries on quota errors)
"""

import time
import json
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import OrderedDict

logger = logging.getLogger(__name__)

# ─── Lazy-loaded LLM clients (shared across all agents) ───────────────────────

_gemini_client = None
_gemini_init_attempted = False

_grok_client = None
_grok_init_attempted = False

_groq_client = None
_groq_init_attempted = False


def _get_gemini_client():
    """Lazy-initialize the Gemini client. Returns None if no API key."""
    global _gemini_client, _gemini_init_attempted
    if _gemini_init_attempted:
        return _gemini_client
    _gemini_init_attempted = True

    try:
        from app.config import settings
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.info("No GEMINI_API_KEY set — Gemini provider unavailable.")
            return None

        from google import genai
        _gemini_client = genai.Client(api_key=api_key)
        logger.info("✅ Gemini API initialized successfully (gemini-2.0-flash).")
        return _gemini_client
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini API: {e}")
        return None


def _get_grok_client():
    """Lazy-initialize the Grok (xAI) client. Returns None if no API key."""
    global _grok_client, _grok_init_attempted
    if _grok_init_attempted:
        return _grok_client
    _grok_init_attempted = True

    try:
        from app.config import settings
        api_key = settings.GROK_API_KEY
        if not api_key:
            logger.info("No GROK_API_KEY set — Grok provider unavailable.")
            return None

        from openai import OpenAI
        _grok_client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        logger.info("✅ Grok (xAI) API initialized successfully (grok-3-mini-fast).")
        return _grok_client
    except Exception as e:
        logger.warning(f"Failed to initialize Grok API: {e}")
        return None


def _get_groq_client():
    """Lazy-initialize the Groq client. Returns None if no API key."""
    global _groq_client, _groq_init_attempted
    if _groq_init_attempted:
        return _groq_client
    _groq_init_attempted = True

    try:
        from app.config import settings
        api_key = settings.GROQ_API_KEY
        if not api_key:
            logger.info("No GROQ_API_KEY set — Groq provider unavailable.")
            return None

        from openai import OpenAI
        _groq_client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        logger.info("✅ Groq API initialized successfully (llama-3.3-70b-versatile).")
        return _groq_client
    except Exception as e:
        logger.warning(f"Failed to initialize Groq API: {e}")
        return None


# ─── LRU Response Cache (shared across all agents) ────────────────────────────

class _LRUCache:
    """Simple LRU cache for LLM responses. Avoids duplicate API calls."""

    def __init__(self, max_size: int = 64, ttl_seconds: int = 300):
        self._cache: OrderedDict[str, tuple] = OrderedDict()  # key -> (response, timestamp)
        self._max_size = max_size
        self._ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _make_key(self, prompt: str, system_prompt: str, provider: str) -> str:
        """Hash prompt + system prompt + provider for a cache key."""
        raw = f"{provider}:{system_prompt[:100]}:{prompt}"
        return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()

    def get(self, prompt: str, system_prompt: str, provider: str) -> Optional[str]:
        key = self._make_key(prompt, system_prompt, provider)
        if key in self._cache:
            response, ts = self._cache[key]
            if time.time() - ts < self._ttl:
                self._cache.move_to_end(key)
                self.hits += 1
                return response
            else:
                del self._cache[key]  # Expired
        self.misses += 1
        return None

    def put(self, prompt: str, system_prompt: str, provider: str, response: str):
        key = self._make_key(prompt, system_prompt, provider)
        self._cache[key] = (response, time.time())
        self._cache.move_to_end(key)
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)


_response_cache = _LRUCache(max_size=64, ttl_seconds=300)


# ─── Circuit Breaker (per provider) ───────────────────────────────────────────

class _CircuitBreaker:
    """
    Prevents wasting API calls on a provider that's down or rate-limited.
    After `threshold` consecutive failures, the circuit opens for `cooldown` seconds.
    """

    def __init__(self, threshold: int = 2, cooldown_seconds: int = 120):
        self._failures: Dict[str, int] = {}
        self._open_until: Dict[str, float] = {}
        self._threshold = threshold
        self._cooldown = cooldown_seconds

    def is_open(self, provider: str) -> bool:
        """Returns True if the circuit is open (provider should not be called)."""
        if provider in self._open_until:
            if time.time() < self._open_until[provider]:
                return True
            else:
                # Cooldown expired — reset
                del self._open_until[provider]
                self._failures[provider] = 0
        return False

    def record_success(self, provider: str):
        self._failures[provider] = 0
        self._open_until.pop(provider, None)

    def record_failure(self, provider: str):
        self._failures[provider] = self._failures.get(provider, 0) + 1
        if self._failures[provider] >= self._threshold:
            self._open_until[provider] = time.time() + self._cooldown
            logger.warning(
                f"⚡ Circuit breaker OPEN for {provider} — "
                f"cooling down for {self._cooldown}s after {self._failures[provider]} failures"
            )


_circuit_breaker = _CircuitBreaker(threshold=2, cooldown_seconds=120)


# ─── Base Agent ────────────────────────────────────────────────────────────────

class BaseAgent(ABC):
    """Base class for all SecureFlow AI agents with multi-LLM support."""

    def __init__(self):
        self.name: str = "base_agent"
        self.description: str = ""
        self.capabilities: List[str] = []
        self.version: str = "1.0.0"
        # Each agent declares its preferred LLM provider: "gemini", "grok", or "groq"
        self.llm_provider: str = "groq"  # Default to Groq
        # Adaptive token limits — smaller for triage, larger for investigation
        self.max_tokens: int = 2048

    @abstractmethod
    def process(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process input and return structured output.
        Must be implemented by each specialized agent.
        """
        pass

    def execute(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute the agent with timing, error handling, and metadata.
        """
        start_time = time.time()

        try:
            result = self.process(input_data, context)
            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "agent": self.name,
                "status": "completed",
                "result": result,
                "confidence": result.get("confidence", 0.0),
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
                "version": self.version,
                "ai_powered": result.get("ai_powered", False),
                "llm_provider": result.get("llm_provider", self.llm_provider),
            }
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "agent": self.name,
                "status": "failed",
                "error": str(e),
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
                "version": self.version,
            }

    # ─── Multi-LLM Call Methods (with cache + circuit breaker + RAG) ──────

    def call_llm(self, prompt: str, system_prompt: str = None, json_mode: bool = False) -> Optional[str]:
        """
        Call the agent's preferred LLM provider with:
          1. RAG knowledge retrieval (inject context into prompt)
          2. Canary token injection into system prompt
          3. Cache check (return cached response if available)
          4. Circuit breaker check (skip provider if it's in cooldown)
          5. Single attempt per provider (no wasted retries on quota errors)
          6. Fast fallback to alternate provider
        """
        sys_prompt = system_prompt or self.get_system_prompt()

        # Inject RAG context into the prompt
        knowledge_context = self.get_knowledge_context(prompt)
        if knowledge_context:
            prompt = f"{knowledge_context}\n\n{prompt}"

        # Inject canary token into system prompt
        try:
            from app.security.canary import inject_canary_into_prompt
            sys_prompt = inject_canary_into_prompt(sys_prompt, session_id=self.name)
        except Exception:
            pass

        # 1. Check cache first
        cached = _response_cache.get(prompt, sys_prompt, self.llm_provider)
        if cached is not None:
            logger.info(f"[{self.name}] 📦 Cache HIT (saved 1 API call)")
            return cached

        # 2. Try preferred provider (if circuit is closed)
        if not _circuit_breaker.is_open(self.llm_provider):
            result = self._call_provider(self.llm_provider, prompt, sys_prompt, json_mode)
            if result is not None:
                _response_cache.put(prompt, sys_prompt, self.llm_provider, result)
                _circuit_breaker.record_success(self.llm_provider)
                return result
            _circuit_breaker.record_failure(self.llm_provider)
        else:
            logger.info(f"[{self.name}] ⚡ Skipping {self.llm_provider} (circuit open)")

        # 3. Fallback to the other provider (if circuit is closed)
        fallback = "groq"
        if self.llm_provider == "groq":
            fallback = "grok"
        elif self.llm_provider == "grok":
            fallback = "gemini"
            
        if not _circuit_breaker.is_open(fallback):
            logger.info(f"[{self.name}] Falling back to {fallback}")
            result = self._call_provider(fallback, prompt, sys_prompt, json_mode)
            if result is not None:
                _response_cache.put(prompt, sys_prompt, fallback, result)
                _circuit_breaker.record_success(fallback)
                return result
            _circuit_breaker.record_failure(fallback)
        else:
            logger.info(f"[{self.name}] ⚡ Skipping fallback {fallback} (circuit open)")

        logger.warning(f"[{self.name}] All LLM providers unavailable. Using heuristic fallback.")
        return None

    def _call_provider(self, provider: str, prompt: str, system_prompt: str, json_mode: bool) -> Optional[str]:
        """Call a specific LLM provider — single attempt, no retry on quota errors."""
        if provider == "gemini":
            return self._call_gemini(prompt, system_prompt, json_mode)
        elif provider == "grok":
            return self._call_grok(prompt, system_prompt, json_mode)
        elif provider == "groq":
            return self._call_groq(prompt, system_prompt, json_mode)
        return None

    def _call_gemini(self, prompt: str, system_prompt: str, json_mode: bool) -> Optional[str]:
        """Call Google Gemini API — single attempt, fail fast on quota errors."""
        client = _get_gemini_client()
        if client is None:
            return None

        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,
                max_output_tokens=self.max_tokens,
            )
            if json_mode:
                config.response_mime_type = "application/json"

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=config,
            )

            if response and response.text:
                logger.info(f"[{self.name}] ✅ Gemini call successful ({len(response.text)} chars)")
                return response.text
            return None

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate" in error_str.lower():
                logger.warning(f"[{self.name}] Gemini rate limited — skipping retries")
            elif "403" in error_str or "permission" in error_str.lower() or "quota" in error_str.lower():
                logger.warning(f"[{self.name}] Gemini permission/quota error — skipping retries")
            else:
                logger.warning(f"[{self.name}] Gemini API error: {e}")
            return None

    def _call_grok(self, prompt: str, system_prompt: str, json_mode: bool) -> Optional[str]:
        """Call xAI Grok API — single attempt, fail fast on quota/permission errors."""
        client = _get_grok_client()
        if client is None:
            return None

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]

            kwargs = {
                "model": "grok-3-mini-fast",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": self.max_tokens,
            }

            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)

            if response and response.choices and response.choices[0].message.content:
                text = response.choices[0].message.content
                logger.info(f"[{self.name}] ✅ Grok call successful ({len(text)} chars)")
                return text
            return None

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                logger.warning(f"[{self.name}] Grok rate limited — skipping retries")
            elif "403" in error_str or "permission" in error_str.lower() or "credit" in error_str.lower():
                logger.warning(f"[{self.name}] Grok permission/credit error — skipping retries")
            else:
                logger.warning(f"[{self.name}] Grok API error: {e}")
            return None

    def _call_groq(self, prompt: str, system_prompt: str, json_mode: bool) -> Optional[str]:
        """Call Groq API — single attempt, fail fast on quota/permission errors."""
        client = _get_groq_client()
        if client is None:
            return None

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]

            kwargs = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": self.max_tokens,
            }

            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)

            if response and response.choices and response.choices[0].message.content:
                text = response.choices[0].message.content
                logger.info(f"[{self.name}] ✅ Groq call successful ({len(text)} chars)")
                return text
            return None

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                logger.warning(f"[{self.name}] Groq rate limited — skipping retries")
            elif "403" in error_str or "permission" in error_str.lower() or "credit" in error_str.lower():
                logger.warning(f"[{self.name}] Groq permission/credit error — skipping retries")
            else:
                logger.warning(f"[{self.name}] Groq API error: {e}")
            return None

    # ─── RAG Knowledge Retrieval ───────────────────────────────────────

    def get_knowledge_context(self, query: str) -> str:
        """
        Retrieve relevant knowledge from the RAG knowledge base.
        Returns formatted context string to prepend to LLM prompt.
        """
        try:
            from app.knowledge.knowledge_base import get_knowledge_base
            from app.config import settings
            kb = get_knowledge_base()
            return kb.get_context_for_prompt(query, top_k=settings.RAG_TOP_K)
        except Exception as e:
            logger.debug(f"[{self.name}] Knowledge retrieval skipped: {e}")
            return ""

    # ─── JSON Helper ───────────────────────────────────────────────────────

    def call_llm_json(self, prompt: str, system_prompt: str = None) -> Optional[Dict]:
        """
        Call LLM and parse the response as JSON.
        Returns parsed dict, or None if unavailable/fails.
        """
        raw = self.call_llm(prompt, system_prompt, json_mode=True)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            try:
                return json.loads(raw)
            except Exception:
                logger.warning(f"[{self.name}] Failed to parse LLM JSON response")
                return None

    # ─── System Prompt ─────────────────────────────────────────────────────

    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        return (
            f"You are the {self.name} agent of SecureFlow AI, "
            f"an autonomous security operations platform. "
            f"Your capabilities: {', '.join(self.capabilities)}. "
            f"Always provide evidence-based analysis with confidence scores. "
            f"Map findings to MITRE ATT&CK framework when applicable. "
            f"Never make unsupported claims. Never claim you have performed actions like "
            f"blocking IPs, quarantining files, or executing commands — you can only recommend. "
            f"Be concise, technical, and actionable."
        )
