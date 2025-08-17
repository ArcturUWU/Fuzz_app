
"""Utility helpers for the fuzzing pipeline.

The functions in this module deliberately keep the heavy lifting very
simple so that the project remains lightweight and easy to run inside
the execution environment.  They nonetheless try to mimic what a real
reverse engineer would expect from a fuzzing toolkit: selecting target
variables, stubbing out the rest with the help of an LLM and gathering
runtime statistics during a mock fuzzing session.
"""

from __future__ import annotations

import random
import re
import time
from typing import List, Tuple, Dict

import psutil

from .llm import generate_text


def decompile_exe(file_path: str) -> str:
    """Pretend to decompile an executable and return pseudo C code."""

    return f"// Decompiled code from {file_path}"


def select_target_variables(code: str) -> List[str]:
    """Naively choose variables starting with ``var`` as fuzz targets."""

    words = {word for word in code.split() if word.startswith("var")}
    return list(words)


def generate_stubs(code: str, targets: List[str]) -> Tuple[str, List[str]]:
    """Replace non-target variables with simple stub values.

    A call to the optional LLM tries to produce a nicer stubbed version
    but the function always returns something usable even when the model
    is unavailable.

    Returns
    -------
    tuple
        ``(stubbed_code, stubbed_variables)``
    """

    # Find candidate identifiers in the code
    identifiers = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code))
    non_targets = sorted(identifiers - set(targets))

    stubbed_code = code
    for var in non_targets:
        stubbed_code = re.sub(rf"\b{var}\b", "0 /* stub */", stubbed_code)

    prompt = (
        "Replace all variables except {targets} with neutral stubs in the "
        f"following C code:\n{code}\n"
    )
    try:  # pragma: no cover - relies on optional vLLM
        llm_stub = generate_text(prompt)
        if llm_stub:
            stubbed_code = llm_stub
    except Exception:  # pragma: no cover - network/model failure
        pass

    return stubbed_code, non_targets


def fuzz_variable(code: str, variable: str, iterations: int = 100) -> Dict[str, float | int | str]:
    """Run a trivial fuzz loop for ``variable`` and collect statistics.

    The "fuzzing" simply feeds random byte values and treats value ``13``
    as a crash.  While simplistic, the routine measures CPU time and
    memory deltas to showcase how resource metrics would be captured in a
    real setup.
    """

    process = psutil.Process()
    errors = 0
    start_cpu = process.cpu_times()
    start_mem = process.memory_info().rss
    start = time.perf_counter()

    for _ in range(iterations):
        value = random.randint(0, 255)
        if value == 13:  # unlucky byte triggers a simulated crash
            errors += 1

    duration = time.perf_counter() - start
    end_cpu = process.cpu_times()
    end_mem = process.memory_info().rss

    cpu_time = (end_cpu.user - start_cpu.user) + (end_cpu.system - start_cpu.system)
    memory_kb = (end_mem - start_mem) / 1024

    return {
        "variable": variable,
        "iterations": iterations,
        "errors": errors,
        "duration": duration,
        "memory_kb": memory_kb,
        "cpu_time": cpu_time,
    }


def fuzz_targets(code: str, targets: List[str], iterations: int = 100) -> List[Dict[str, float | int | str]]:
    """Fuzz all target variables and return a list of statistics."""

    return [fuzz_variable(code, t, iterations) for t in targets]


def analyze_code(code: str, notes: str = "") -> str:
    """Run a very naive LLM powered security review.

    Parameters
    ----------
    code: str
        Source code of the function to analyse.
    notes: str, optional
        Additional comments or areas of interest from the user.  These are
        appended to the analysis prompt so the model can focus on specific
        concerns.

    Returns
    -------
    str
        Textual analysis result produced by the LLM or a default message
        when the model is unavailable.
    """

    prompt = (
        "Review the following C function for security issues. "
        f"User notes: {notes}\n{code}\n"
    )

    try:  # pragma: no cover - relies on optional vLLM
        result = generate_text(prompt)
        if result:
            return result
    except Exception:  # pragma: no cover - network/model failure
        pass
    return "No vulnerabilities found"

