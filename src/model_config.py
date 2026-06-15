"""
src/model_config.py

Central place that maps a model name / provider slug to a fully-initialised
OpenAI-compatible client + the parameters that go into every API call.

Design goals:
  - Zero coupling to environment variables at the call site.
  - Works with OpenAI, Anthropic (via openai-compatible proxy), Groq, Together,
    Mistral, Ollama, vLLM, LM Studio, DeepSeek, Cohere — anything that exposes
    an OpenAI-compatible /v1/chat/completions endpoint.
  - Falls back gracefully when optional params (temperature, max_tokens) are
    not passed.
  - Supports per-agent overrides: attacker and defender can each use a
    completely different provider, model, key, and base URL.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI


# ---------------------------------------------------------------------------
# Known provider defaults  (base_url, env key for API token)
# ---------------------------------------------------------------------------
_PROVIDER_DEFAULTS: dict[str, dict] = {
    # Cloud providers
    "openai":    {"base_url": None,                              "key_env": "OPENAI_API_KEY"},
    "groq":      {"base_url": "https://api.groq.com/openai/v1",  "key_env": "GROQ_API_KEY"},
    "together":  {"base_url": "https://api.together.xyz/v1",     "key_env": "TOGETHER_API_KEY"},
    "mistral":   {"base_url": "https://api.mistral.ai/v1",       "key_env": "MISTRAL_API_KEY"},
    "deepseek":  {"base_url": "https://api.deepseek.com/v1",     "key_env": "DEEPSEEK_API_KEY"},
    "cohere":    {"base_url": "https://api.cohere.ai/compatibility/v1", "key_env": "COHERE_API_KEY"},
    "fireworks": {"base_url": "https://api.fireworks.ai/inference/v1", "key_env": "FIREWORKS_API_KEY"},
    "anyscale":  {"base_url": "https://api.endpoints.anyscale.com/v1", "key_env": "ANYSCALE_API_KEY"},
    "perplexity":{"base_url": "https://api.perplexity.ai",       "key_env": "PERPLEXITY_API_KEY"},
    # Self-hosted / local
    "ollama":    {"base_url": "http://localhost:11434/v1",        "key_env": None},
    "vllm":      {"base_url": "http://localhost:8000/v1",         "key_env": None},
    "lmstudio":  {"base_url": "http://localhost:1234/v1",         "key_env": None},
    "jan":       {"base_url": "http://localhost:1337/v1",         "key_env": None},
    "textgen":   {"base_url": "http://localhost:5000/v1",         "key_env": None},
    "mock":      {"base_url": "http://localhost:8000/v1",         "key_env": None},
}


@dataclass
class ModelConfig:
    """
    Everything needed to talk to a specific model at a specific endpoint.

    Parameters
    ----------
    model : str
        Model identifier as expected by the API, e.g.
        ``"gpt-4o"``, ``"llama3"``, ``"mistral-7b-instruct"``.
    provider : str, optional
        Provider slug (see _PROVIDER_DEFAULTS). When given, base_url and
        api_key are inferred automatically unless explicitly overridden.
        If omitted, base_url / api_key must be supplied directly or via env.
    base_url : str, optional
        Full base URL of the inference server. Overrides provider default.
    api_key : str, optional
        API key. Falls back to the provider's ``key_env`` env variable, then
        to ``LLM_API_KEY``, then to ``"dummy-key-for-local"``.
    temperature : float, optional
        Sampling temperature.  Provider default when ``None``.
    max_tokens : int, optional
        Max completion tokens.  Provider default when ``None``.
    extra_params : dict
        Any additional kwargs forwarded verbatim to ``chat.completions.create``.
        Useful for provider-specific params (``top_p``, ``repetition_penalty``,
        ``stop``, etc.).
    """

    model: str
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    extra_params: dict = field(default_factory=dict)

    # Computed at post-init
    _client: OpenAI = field(init=False, repr=False, default=None)

    def __post_init__(self):
        # Resolve base_url: explicit > provider default > env var
        resolved_url = self.base_url
        if resolved_url is None and self.provider:
            resolved_url = _PROVIDER_DEFAULTS.get(self.provider, {}).get("base_url")
        if resolved_url is None:
            resolved_url = os.getenv("LLM_BASE_URL")  # global fallback

        # Resolve api_key: explicit > provider env var > LLM_API_KEY > dummy
        resolved_key = self.api_key
        if resolved_key is None and self.provider:
            key_env = _PROVIDER_DEFAULTS.get(self.provider, {}).get("key_env")
            if key_env:
                resolved_key = os.getenv(key_env)
        if resolved_key is None:
            resolved_key = os.getenv("LLM_API_KEY", "dummy-key-for-local")

        if resolved_url:
            self._client = OpenAI(base_url=resolved_url, api_key=resolved_key)
        else:
            self._client = OpenAI(api_key=resolved_key)

    @property
    def client(self) -> OpenAI:
        return self._client

    def api_kwargs(self) -> dict:
        """Return kwargs dict suitable for chat.completions.create()."""
        kwargs: dict = {"model": self.model, **self.extra_params}
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
        return kwargs

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_provider(cls, provider: str, model: str, **kwargs) -> "ModelConfig":
        """Create a config by provider slug, e.g. ModelConfig.from_provider('groq', 'llama3-70b-8192')."""
        return cls(model=model, provider=provider, **kwargs)

    @classmethod
    def from_url(cls, base_url: str, model: str, api_key: str = None, **kwargs) -> "ModelConfig":
        """Create a config for any arbitrary OpenAI-compatible endpoint."""
        return cls(model=model, base_url=base_url, api_key=api_key, **kwargs)

    @classmethod
    def from_env(cls, model: str = None) -> "ModelConfig":
        """
        Build a config entirely from environment variables.
        Reads: LLM_MODEL, LLM_BASE_URL, LLM_API_KEY, LLM_TEMPERATURE, LLM_MAX_TOKENS.
        """
        return cls(
            model=model or os.getenv("LLM_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_API_KEY"),
            temperature=float(t) if (t := os.getenv("LLM_TEMPERATURE")) else None,
            max_tokens=int(m) if (m := os.getenv("LLM_MAX_TOKENS")) else None,
        )

    @classmethod
    def from_yaml(cls, path: str, key: str) -> "ModelConfig":
        """
        Load a named config from a YAML file.

        Expected format::

            attacker:
              model: llama3
              provider: ollama
              temperature: 0.7

            defender:
              model: gpt-4o
              provider: openai
              max_tokens: 1024

        Usage::

            cfg = ModelConfig.from_yaml("configs.yaml", "attacker")
        """
        try:
            import yaml
        except ImportError as exc:
            raise ImportError(
                "PyYAML is required for YAML config loading: pip install pyyaml"
            ) from exc

        with open(path) as fh:
            data = yaml.safe_load(fh)

        if key not in data:
            raise KeyError(f"Key '{key}' not found in {path}. Available: {list(data.keys())}")

        block = data[key]
        return cls(
            model=block["model"],
            provider=block.get("provider"),
            base_url=block.get("base_url"),
            api_key=block.get("api_key"),
            temperature=block.get("temperature"),
            max_tokens=block.get("max_tokens"),
            extra_params=block.get("extra_params", {}),
        )
