"""Простой Todo API для демонстрации процесса релизов."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Todo API", version="0.1.0")

# Имитация хранилища в памяти
todos: list[dict] = []
_next_id: int = 1


class TodoCreate(BaseModel):
    title: str
    completed: bool = False


class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool


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
def list_todos() -> list[TodoResponse]:
    """Получить список всех задач."""
    return [TodoResponse(**t) for t in todos]


@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int) -> TodoResponse:
    """Получить задачу по ID."""
    for todo in todos:
        if todo["id"] == todo_id:
            return TodoResponse(**todo)
    raise HTTPException(status_code=404, detail="Todo not found")