#!/usr/bin/env python3
"""
Скрипт ручного релиза.
Имитирует процесс, который мы будем автоматизировать в следующих лекциях.

Использование:
    python scripts/release.py
"""

import datetime
import hashlib
import shutil
import sys
import tarfile
from pathlib import Path

# Конфигурация 
PROJECT_NAME = "todo-api"
VERSION = "0.1.0"  # В реальном проекте читали бы из pyproject.toml
BUILD_DIR = Path("dist")
RELEASE_LOG = Path("release_log.md")


def get_version() -> str:
    """Читает версию из pyproject.toml (упрощённый парсинг)."""
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print("Файл pyproject.toml не найден!")
        sys.exit(1)

    for line in pyproject.read_text().splitlines():
        if line.strip().startswith("version"):
            # version = "0.1.0" → 0.1.0
            return line.split("=")[1].strip().strip('"')
    return VERSION


def calculate_checksum(file_path: Path) -> str:
    """Вычисляет SHA-256 хеш файла для контроля целостности артефакта."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def build_artifact(version: str) -> Path:
    """Упаковывает исходный код в .tar.gz архив (артефакт релиза)."""
    print(f"Собираю артефакт: {PROJECT_NAME}-{version}")

    BUILD_DIR.mkdir(exist_ok=True)
    artifact_name = f"{PROJECT_NAME}-{version}.tar.gz"
    artifact_path = BUILD_DIR / artifact_name

    with tarfile.open(artifact_path, "w:gz") as tar:
        tar.add("src", arcname="src")
        tar.add("pyproject.toml")

    print(f"Артефакт создан: {artifact_path}")
    return artifact_path


def generate_release_notes(version: str, artifact_path: Path) -> str:
    """Генерирует примитивный лог релиза."""
    checksum = calculate_checksum(artifact_path)
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    notes = f"""# Release Notes

## {PROJECT_NAME} v{version}

- **Дата релиза:** {timestamp}
- **Артефакт:** `{artifact_path.name}`
- **SHA-256:** `{checksum}`
- **Размер:** {artifact_path.stat().st_size} байт

### Что входит в релиз
- Базовый Todo API (health, CRUD для задач)
- Модульные тесты

### Статус
Готов к развёртыванию на Staging
"""
    return notes


def validate_artifact(artifact_path: Path) -> bool:
    """Проверяет, что артефакт существует и не пуст."""
    if not artifact_path.exists():
        print("Артефакт не найден!")
        return False
    if artifact_path.stat().st_size == 0:
        print("Артефакт пуст!")
        return False
    print(f"Артефакт валиден ({artifact_path.stat().st_size} байт)")
    return True


def main() -> None:
    """Основной процесс ручного релиза."""
    print("=" * 60)
    print(f"ПРОЦЕСС РЕЛИЗА: {PROJECT_NAME}")
    print("=" * 60)

    # Шаг 1: Определение версии
    version = get_version()
    print(f"\nВерсия релиза: {version}")

    # Шаг 2: Сборка артефакта
    print("\nЭтап сборки...")
    artifact_path = build_artifact(version)

    # Шаг 3: Валидация
    print("\nЭтап валидации...")
    if not validate_artifact(artifact_path):
        print("Релиз прерван: артефакт не прошёл валидацию.")
        sys.exit(1)

    # Шаг 4: Генерация release notes
    print("\nГенерация release notes...")
    notes = generate_release_notes(version, artifact_path)
    RELEASE_LOG.write_text(notes)
    print(f"Лог записан в {RELEASE_LOG}")

    # Шаг 5: Имитация деплоя
    print("\n Этап развёртывания (имитация)...")
    print("   Копирую артефакт на 'сервер'...")
    # В реальном мире здесь был бы scp / docker push / ansible
    # Мы просто подтверждаем, что артефакт готов
    print(f"    Артефакт {artifact_path.name} готов к деплою на Staging")

    print("\n" + "=" * 60)
    print(" РЕЛИЗ УСПЕШНО ЗАВЕРШЁН (в ручном режиме)")
    print("=" * 60)
    print("\n⚠  На следующих лекциях мы автоматизируем каждый из этих шагов!")


if __name__ == "__main__":
    main()