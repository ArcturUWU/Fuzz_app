import os
import sys

from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "fuzz_app.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

sys.path.append(BASE_DIR)

from app.main import app

client = TestClient(app)


def test_list_projects_initial():
    response = client.get("/projects")
    assert response.status_code == 200
    assert response.json() == []


def test_full_pipeline():
    # create project
    resp = client.post("/projects", json={"name": "demo"})
    project_id = resp.json()["id"]

    code = "int main(){ int var1 = 0; int var2 = 1; return var1 + var2; }"
    up = client.post(
        f"/projects/{project_id}/upload-code",
        json={"filename": "demo.c", "content": code},
    )
    assert up.status_code == 200

    fuzz = client.post(f"/projects/{project_id}/fuzz").json()
    assert fuzz["results"][0]["variable"].startswith("var")

    analysis = client.post(f"/projects/{project_id}/analyze")
    assert analysis.status_code == 200

    report = client.get(f"/projects/{project_id}/report").json()
    assert report["fuzz_stats"]
