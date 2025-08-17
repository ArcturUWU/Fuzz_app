# Fuzz_app

A quick web application for reverse engineering and mock generation.

## Features

- Manage multiple projects
- Upload executables or C-like code
- Naive decompilation and stub generation using an LLM endpoint
- Basic fuzzing and vulnerability analysis placeholders
- SQLite storage and simple reporting

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Testing

```bash
pytest
```
