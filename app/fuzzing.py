"""Utility helpers for the fuzzing pipeline."""

from typing import List

from .llm import generate_text


def decompile_exe(file_path: str) -> str:
    """Pretend to decompile an executable and return pseudo C code."""
    return f"// Decompiled code from {file_path}"


def select_target_variables(code: str) -> List[str]:
    """Naively choose variables starting with ``var`` as fuzz targets."""
    words = {word for word in code.split() if word.startswith("var")}
    return list(words)


def generate_stubs(code: str, targets: List[str]) -> str:
    """Use an LLM to create stubs for non-target variables."""
    prompt = (
        "Replace all variables except {targets} with stubs in the following "
        f"code:\n{code}"
    )
    try:
        return generate_text(prompt)
    except Exception:  # pragma: no cover - network/model failure
        return "/* stubbed code */"


def fuzz_variable(code: str, variable: str) -> str:
    """Placeholder fuzzing process for a single variable."""
    return f"Fuzzing {variable} in code..."


def analyze_code(code: str) -> str:
    """Placeholder security analysis returning a constant string."""
    return "No vulnerabilities found"
