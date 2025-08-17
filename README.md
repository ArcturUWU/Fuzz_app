# Fuzz_app

Minimal web application for organising fuzzing and security analysis
experiments.  The backend is built with FastAPI and offers both a REST
API and a VSCode‑inspired web interface featuring a Monaco code editor
and tabbed workflow for each project.

## Features

- Create and browse multiple projects via the web interface
- VSCode-style workspace with left-hand file navigation and Monaco editor
  for quick switching between source files
- Naive decompilation, user-selectable target variables and automatic
  stub generation via an optional vLLM-powered model
- In-browser fuzzing results that display CPU and memory utilisation and
  show code before/after stubbing
- LLM-backed analysis pane with room for user notes and feedback
- SQLite storage and project reports rendered in the browser with a PDF
  export option

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000> to access the interface.

An end-to-end mock pipeline is available in `examples/mock_pipeline.py`
and exercises the REST API to create a project, upload code, fuzz,
analyse and retrieve the final report:

```bash
python examples/mock_pipeline.py
```

## Suggested stacks

### Fuzzing
- [AFL++](https://github.com/AFLplusplus/AFLplusplus) for coverage guided
  fuzzing of binaries
- [libFuzzer](https://llvm.org/docs/LibFuzzer.html) or
  [BooFuzz](https://github.com/jtpereyda/boofuzz) for API and network fuzzing
- [Radamsa](https://gitlab.com/akihe/radamsa) for mutation‑based input
  generation

### Decompilation
- [Ghidra](https://ghidra-sre.org/) or
  [Binary Ninja](https://binary.ninja/) for interactive reverse
  engineering
- [radare2](https://rada.re/) for scripted analysis

### LLM integration
The `app/llm.py` helper tries to use vLLM with a small open source
model (`facebook/opt-125m`) to generate code stubs.  If vLLM or the
model weights are not available the function falls back to returning a
static stub so the rest of the application still works.  To enable real
generation install vLLM and place the desired model weights on disk:

```bash
pip install vllm
```

## Testing

```bash
pytest
```
