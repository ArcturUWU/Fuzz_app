"""Light wrapper around vLLM for text generation.

This module attempts to use `vllm` if it is installed.  If the
library or model weights are unavailable the `generate_text` function
falls back to returning a static stub string so that the rest of the
application continues to work.
"""
from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - optional dependency
    from vllm import LLM, SamplingParams  # type: ignore
    _VLLM_AVAILABLE = True
except Exception:  # pragma: no cover - import failure
    LLM = None  # type: ignore
    SamplingParams = None  # type: ignore
    _VLLM_AVAILABLE = False

_model: Optional[LLM] = None


def _get_model() -> Optional[LLM]:  # pragma: no cover - heavy to test
    """Lazily initialise the LLM model when vLLM is available."""
    global _model
    if not _VLLM_AVAILABLE:
        return None
    if _model is None:
        # A small open source model keeps resource usage modest.
        _model = LLM(model="facebook/opt-125m")
    return _model


def generate_text(prompt: str, max_tokens: int = 128) -> str:
    """Generate text from a prompt using vLLM when possible.

    Parameters
    ----------
    prompt: str
        The prompt to send to the language model.
    max_tokens: int
        Maximum number of tokens to generate.
    """
    model = _get_model()
    if model is None:  # pragma: no cover - fallback path
        return "/* stubbed code */"
    params = SamplingParams(temperature=0.7, max_tokens=max_tokens)
    outputs = model.generate(prompt, params)
    return outputs[0].outputs[0].text.strip()
