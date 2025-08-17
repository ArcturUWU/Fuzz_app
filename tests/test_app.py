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


def test_deletion():
    resp = client.post("/projects", json={"name": "todelete"})
    pid = resp.json()["id"]
    file_resp = client.post(
        f"/projects/{pid}/upload-code",
        json={"filename": "a.c", "content": "int x=0;"},
    ).json()
    fid = file_resp["id"]
    del_file = client.delete(f"/projects/{pid}/files/{fid}")
    assert del_file.status_code == 200
    report = client.get(f"/projects/{pid}/report").json()
    assert report["files"] == []
    del_proj = client.delete(f"/projects/{pid}")
    assert del_proj.status_code == 200
    projects = client.get("/projects").json()
    assert all(p["id"] != pid for p in projects)


def test_get_and_update_file():
    resp = client.post("/projects", json={"name": "editproj"})
    pid = resp.json()["id"]
    file_resp = client.post(
        f"/projects/{pid}/upload-code",
        json={"filename": "a.c", "content": "int x=0;"},
    ).json()
    fid = file_resp["id"]
    fetched = client.get(f"/projects/{pid}/files/{fid}").json()
    assert fetched["filename"] == "a.c"
    updated = client.put(
        f"/projects/{pid}/files/{fid}",
        json={"filename": "b.c", "content": "int y=1;"},
    ).json()
    assert updated["filename"] == "b.c"
    fetched2 = client.get(f"/projects/{pid}/files/{fid}").json()
    assert fetched2["filename"] == "b.c"
    assert "int y=1;" in fetched2["content"]


def test_save_file_blank_id():
    resp = client.post("/projects", json={"name": "blankid"})
    pid = resp.json()["id"]
    # simulate form submission with empty file_id
    save = client.post(
        f"/projects/{pid}/save-file",
        data={"filename": "new.c", "content": "int z=2;", "file_id": ""},
    )
    assert save.status_code == 200
    projects = client.get("/projects").json()
    proj = next(p for p in projects if p["id"] == pid)
    assert any(f["filename"] == "new.c" for f in proj["files"])
