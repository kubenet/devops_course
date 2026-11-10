"""Простой Todo API для демонстрации процесса релизов."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="Todo API", version="0.2.0")

# Имитация хранилища в памяти
todos: list[dict] = []
_next_id: int = 1


# ─── Схемы данных (модели) ────────────────────────────────────────────────────

class TodoCreate(BaseModel):
    """Модель для создания задачи."""
    title: str
    completed: bool = False


class TodoUpdate(BaseModel):
    """Модель для полного обновления задачи (PUT)."""
    title: str
    completed: bool


class TodoResponse(BaseModel):
    """Модель ответа с задачей."""
    id: int
    title: str
    completed: bool


class StatsResponse(BaseModel):
    """Модель ответа со статистикой."""
    total: int
    completed: int
    pending: int
    completion_rate: float


# ─── Вспомогательная функция ──────────────────────────────────────────────────

def _find_todo(todo_id: int) -> dict:
    """
    Ищет задачу по ID во внутреннем хранилище.

    Аналогия: как библиотекарь ищет книгу по инвентарному номеру —
    если не находит, сообщает об ошибке.

    Raises:
        HTTPException 404, если задача не найдена.
    """
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    raise HTTPException(status_code=404, detail=f"Todo with id={todo_id} not found")


# ─── Существующие роуты (из Лекции 1) ─────────────────────────────────────────

@app.get("/health")
def health_check() -> dict:
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "version": app.version}


@app.post("/todos", response_model=TodoResponse, status_code=201)
def create_todo(todo: TodoCreate) -> TodoResponse:
    """Создать новую задачу."""
    global _next_id
    new_todo = {"id": _next_id, "title": todo.title, "completed": todo.completed}
    todos.append(new_todo)
    _next_id += 1
    return TodoResponse(**new_todo)


@app.get("/todos", response_model=list[TodoResponse])
def list_todos(
    completed: bool | None = Query(default=None, description="Фильтр по статусу")
) -> list[TodoResponse]:
    """Получить список всех задач с опциональной фильтрацией."""
    if completed is None:
        return [TodoResponse(**t) for t in todos]
    return [TodoResponse(**t) for t in todos if t["completed"] == completed]


@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int) -> TodoResponse:
    """Получить задачу по ID."""
    todo = _find_todo(todo_id)
    return TodoResponse(**todo)


# ─── НОВЫЕ РОУТЫ ──────────────────────────────────────────────────────────────

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_data: TodoUpdate) -> TodoResponse:
    """
    Полностью обновить существующую задачу.

    Аналогия: вы переписываете всю страницу в блокноте —
    старое содержимое исчезает, появляется новое.
    Если хотите изменить только одно поле — это был бы PATCH,
    но мы используем PUT для простоты.

    Параметры:
        todo_id: уникальный идентификатор задачи.
        todo_data: новые значения полей (обязательны все).

    Возвращает:
        Обновлённую задачу.

    Ошибки:
        404 — задача с таким ID не существует.
        422 — тело запроса не соответствует схеме.
    """
    todo = _find_todo(todo_id)

    # Полная замена полей (семантика PUT)
    todo["title"] = todo_data.title
    todo["completed"] = todo_data.completed

    return TodoResponse(**todo)


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int) -> None:
    """
    Удалить задачу по ID.

    Аналогия: вырвать страницу из блокнота.
    После удаления страница не существует — вернуть нечего.

    Возвращает:
        204 No Content — успешное удаление без тела ответа.

    Ошибки:
        404 — задача с таким ID не существует.
    """
    global todos
    todo = _find_todo(todo_id)  # Проверит существование, бросит 404 если нет
    todos.remove(todo)
    # status_code=204 означает: «сделано, но возвращать нечего»


@app.get("/stats", response_model=StatsResponse)
def get_stats() -> StatsResponse:
    """
    Получить статистику по всем задачам.

    Аналогия: дашборд на стене офиса —
    видно, сколько всего задач, сколько завершено, сколько в работе.

    Возвращает:
        - total: общее количество задач
        - completed: количество завершённых
        - pending: количество незавершённых
        - completion_rate: доля завершённых (0.0 – 1.0)
    """
    total = len(todos)
    completed = sum(1 for t in todos if t["completed"])
    pending = total - completed
    rate = round(completed / total, 4) if total > 0 else 0.0

    return StatsResponse(
        total=total,
        completed=completed,
        pending=pending,
        completion_rate=rate,
    )