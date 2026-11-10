"""
Модульные тесты для Todo API.
Покрывают все роуты, включая 3 новых.

Запуск:
    pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

from todo_api.app import app, todos

client = TestClient(app)


# ─── Фикстуры ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_state():
    """
    Сбрасывает состояние хранилища перед каждым тестом.

    Аналогия: перед каждым экспериментом учёный стерилизует пробирки,
    чтобы результаты предыдущего опыта не влияли на текущий.
    """
    todos.clear()
    yield
    todos.clear()


@pytest.fixture
def sample_todo() -> dict:
    """Создаёт одну задачу и возвращает её данные."""
    response = client.post("/todos", json={"title": "Изучить CI/CD"})
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def multiple_todos() -> list[dict]:
    """Создаёт три задачи: 2 незавершённые, 1 завершённая."""
    client.post("/todos", json={"title": "Задача A"})
    client.post("/todos", json={"title": "Задача B", "completed": True})
    client.post("/todos", json={"title": "Задача C"})
    return client.get("/todos").json()


# ─── Тесты существующих роутов ────────────────────────────────────────────────

class TestHealthCheck:
    """Тесты эндпоинта /health."""

    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_contains_version(self):
        response = client.get("/health")
        assert "version" in response.json()


class TestCreateTodo:
    """Тесты создания задачи."""

    def test_create_returns_201(self):
        response = client.post("/todos", json={"title": "Новая задача"})
        assert response.status_code == 201

    def test_create_returns_correct_fields(self):
        response = client.post("/todos", json={"title": "Изучить DevOps"})
        data = response.json()
        assert data["title"] == "Изучить DevOps"
        assert data["completed"] is False
        assert isinstance(data["id"], int)

    def test_create_increments_id(self):
        r1 = client.post("/todos", json={"title": "Первая"})
        r2 = client.post("/todos", json={"title": "Вторая"})
        assert r2.json()["id"] == r1.json()["id"] + 1


class TestListTodos:
    """Тесты получения списка задач."""

    def test_empty_list(self):
        response = client.get("/todos")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_all(self, multiple_todos):
        response = client.get("/todos")
        assert len(response.json()) == 3

    def test_filter_completed(self, multiple_todos):
        response = client.get("/todos", params={"completed": True})
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Задача B"

    def test_filter_pending(self, multiple_todos):
        response = client.get("/todos", params={"completed": False})
        assert len(response.json()) == 2


class TestGetTodo:
    """Тесты получения одной задачи."""

    def test_get_existing(self, sample_todo):
        todo_id = sample_todo["id"]
        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Изучить CI/CD"

    def test_get_nonexistent_returns_404(self):
        response = client.get("/todos/9999")
        assert response.status_code == 404


# ─── Тесты НОВЫХ роутов ───────────────────────────────────────────────────────

class TestUpdateTodo:
    """Тесты PUT /todos/{todo_id} — полное обновление."""

    def test_update_title_and_status(self, sample_todo):
        """Обновляем и заголовок, и статус одновременно."""
        todo_id = sample_todo["id"]
        response = client.put(
            f"/todos/{todo_id}",
            json={"title": "Обновлённая задача", "completed": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Обновлённая задача"
        assert data["completed"] is True
        assert data["id"] == todo_id  # ID не должен меняться

    def test_update_preserves_id(self, sample_todo):
        """Убеждаемся, что PUT не создаёт новую запись."""
        todo_id = sample_todo["id"]
        client.put(f"/todos/{todo_id}", json={"title": "Новое имя", "completed": False})

        # В списке по-прежнему один элемент с тем же ID
        all_todos = client.get("/todos").json()
        assert len(all_todos) == 1
        assert all_todos[0]["id"] == todo_id

    def test_update_nonexistent_returns_404(self):
        """PUT к несуществующей задаче → 404."""
        response = client.put(
            "/todos/9999",
            json={"title": "Призрак", "completed": False},
        )
        assert response.status_code == 404

    def test_update_with_invalid_body_returns_422(self, sample_todo):
        """Пропускаем обязательное поле → 422 Unprocessable Entity."""
        todo_id = sample_todo["id"]
        response = client.put(f"/todos/{todo_id}", json={"title": "Без completed"})
        assert response.status_code == 422

    def test_update_reflects_in_get(self, sample_todo):
        """После PUT данные видны при последующем GET."""
        todo_id = sample_todo["id"]
        client.put(f"/todos/{todo_id}", json={"title": "После обновления", "completed": True})

        response = client.get(f"/todos/{todo_id}")
        assert response.json()["title"] == "После обновления"


class TestDeleteTodo:
    """Тесты DELETE /todos/{todo_id} — удаление."""

    def test_delete_returns_204(self, sample_todo):
        """Успешное удаление возвращает 204 без тела."""
        todo_id = sample_todo["id"]
        response = client.delete(f"/todos/{todo_id}")
        assert response.status_code == 204
        assert response.text == ""  # Тело пустое

    def test_delete_removes_from_list(self, multiple_todos):
        """После удаления задача исчезает из списка."""
        target_id = multiple_todos[0]["id"]
        client.delete(f"/todos/{target_id}")

        remaining = client.get("/todos").json()
        assert len(remaining) == 2
        assert all(t["id"] != target_id for t in remaining)

    def test_delete_nonexistent_returns_404(self):
        """Удаление несуществующей задачи → 404."""
        response = client.delete("/todos/9999")
        assert response.status_code == 404

    def test_delete_then_get_returns_404(self, sample_todo):
        """GET после DELETE → 404."""
        todo_id = sample_todo["id"]
        client.delete(f"/todos/{todo_id}")

        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 404

    def test_delete_all_leaves_empty_list(self, multiple_todos):
        """Удаляем все задачи → список пуст."""
        for todo in multiple_todos:
            client.delete(f"/todos/{todo['id']}")

        assert client.get("/todos").json() == []


class TestStats:
    """Тесты GET /stats — статистика."""

    def test_stats_empty(self):
        """Когда задач нет, все показатели нулевые."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["completed"] == 0
        assert data["pending"] == 0
        assert data["completion_rate"] == 0.0

    def test_stats_all_pending(self):
        """Все задачи незавершены → rate = 0.0."""
        client.post("/todos", json={"title": "A"})
        client.post("/todos", json={"title": "B"})

        data = client.get("/stats").json()
        assert data["total"] == 2
        assert data["completed"] == 0
        assert data["pending"] == 2
        assert data["completion_rate"] == 0.0

    def test_stats_all_completed(self):
        """Все задачи завершены → rate = 1.0."""
        client.post("/todos", json={"title": "A", "completed": True})
        client.post("/todos", json={"title": "B", "completed": True})

        data = client.get("/stats").json()
        assert data["total"] == 2
        assert data["completed"] == 2
        assert data["pending"] == 0
        assert data["completion_rate"] == 1.0

    def test_stats_mixed(self, multiple_todos):
        """Смешанный сценарий: 2 в работе, 1 завершена."""
        data = client.get("/stats").json()
        assert data["total"] == 3
        assert data["completed"] == 1
        assert data["pending"] == 2
        assert abs(data["completion_rate"] - 0.3333) < 0.001

    def test_stats_updates_after_completion(self, sample_todo):
        """Статистика меняется после обновления задачи."""
        todo_id = sample_todo["id"]

        # До обновления
        before = client.get("/stats").json()
        assert before["completed"] == 0

        # Завершаем задачу
        client.put(f"/todos/{todo_id}", json={"title": "Готово", "completed": True})

        # После обновления
        after = client.get("/stats").json()
        assert after["completed"] == 1
        assert after["completion_rate"] == 1.0

    def test_stats_updates_after_delete(self, multiple_todos):
        """Статистика пересчитывается после удаления."""
        # Удаляем завершённую задачу (Задача B)
        target = next(t for t in multiple_todos if t["completed"])
        client.delete(f"/todos/{target['id']}")

        data = client.get("/stats").json()
        assert data["total"] == 2
        assert data["completed"] == 0
        assert data["pending"] == 2