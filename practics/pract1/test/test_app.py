"""Модульные тесты для Todo API."""

from fastapi.testclient import TestClient
from todo_api.app import app

client = TestClient(app)


def test_health_check():
    """Проверяем, что эндпоинт здоровья возвращает статус ок."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_create_todo():
    """Проверяем создание задачи."""
    response = client.post("/todos", json={"title": "Изучить DevOps"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Изучить DevOps"
    assert data["completed"] is False
    assert "id" in data