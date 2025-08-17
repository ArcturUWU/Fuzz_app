# Fuzz_app

Minimal web application for organising fuzzing and security analysis
experiments.  The backend is built with FastAPI and offers both a REST
API and a VSCode‑inspired web interface featuring a Monaco code editor
and tabbed workflow for each project.

## Features

- Create and browse multiple projects via the web interface
- VSCode-style editor pane with EXE or source upload for each project

- Naive decompilation, target variable selection and stub generation
  via an LLM powered by [vLLM](https://github.com/vllm-project/vllm)
- Simple fuzzing and vulnerability analysis placeholders
- SQLite storage and project reports rendered in the browser

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000> to access the interface.

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
