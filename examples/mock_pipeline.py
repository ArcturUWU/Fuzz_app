"""Run a full mock pipeline against the REST API.

The script creates a project, uploads a small C snippet, performs
stub generation and fuzzing, triggers analysis and finally prints the
project report.  It uses FastAPI's ``TestClient`` so no server has to be
running in advance.
"""

from fastapi.testclient import TestClient

from app.main import app


def run() -> None:
    client = TestClient(app)

    resp = client.post("/projects", json={"name": "demo"})
    project_id = resp.json()["id"]

    code = "int main(){ int varA = 0; int varB = 1; return varA + varB; }"
    client.post(
        f"/projects/{project_id}/upload-code",
        json={"filename": "demo.c", "content": code},
    )

    fuzz = client.post(f"/projects/{project_id}/fuzz").json()
    print("Fuzzing:", fuzz)

    analysis = client.post(f"/projects/{project_id}/analyze").json()
    print("Analysis:", analysis)

    report = client.get(f"/projects/{project_id}/report").json()
    print("Report:", report)


if __name__ == "__main__":  # pragma: no cover - manual example
    run()

