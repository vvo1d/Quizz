# Quiz App

Flask-приложение для создания и прохождения квизов.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Для Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Запуск

```bash
python run.py
```

Приложение будет доступно по адресу:

```text
http://127.0.0.1:5000
```

## Инициализация базы вручную

Обычно база создаётся автоматически при запуске. Также можно выполнить:

```bash
flask --app run.py init-db
```