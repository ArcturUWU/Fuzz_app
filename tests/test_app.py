import os
import sys

from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.main import app

client = TestClient(app)


def test_list_projects_initial():
    response = client.get("/projects")
    assert response.status_code == 200
    assert response.json() == []
