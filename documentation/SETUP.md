# 🔧 Настройка окружения для работы с переводом

## 📋 Требования
- **Python 3.8+**

## Активация
```bash
source venv/bin/activate
```

## 🚀 Пошаговая установка
### 1. Клонирование репозитория
```bash
cd /path/to/game/directory
# копируем файлы репозитория сюда
```

### 2. Создание виртуального окружения
Виртуальное окружение изолирует зависимости проекта от системных пакетов.

```bash
# Создать venv (выполнить один раз)
python3 -m venv venv

# Активировать venv (выполнять при каждом запуске терминала)
source venv/bin/activate

# После активации в терминале появится префикс (venv)
```

**Для Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
# Убедитесь, что venv активирован!
# Должен быть префикс (venv) в начале строки

pip install --upgrade pip
pip install unrpa
```

### 4. Проверка установки

```bash
# Проверить Python
python3 --version
# Должно быть: Python 3.8 или выше

# Проверить unrpa
python3 -m unrpa --version
# Должна показаться версия unrpa
```

## ✅ Готово к работе!

Теперь можно использовать инструменты:

```bash
# ВСЕГДА активируйте venv перед работой
source venv/bin/activate
```

## 🛠️ Деактивация venv

Когда закончили работу:

```bash
deactivate
```

Префикс `(venv)` исчезнет.

## ❓ Решение проблем

### Проблема: `unrpa` не найден
```bash
# Убедитесь, что venv активирован
source venv/bin/activate

# Переустановите unrpa
pip uninstall unrpa
pip install unrpa
```

### Проблема: `ModuleNotFoundError`
```bash
# Активируйте venv
source venv/bin/activate

# Проверьте, что находитесь в правильной папке
pwd  # Должно показать путь к папке Ravager
```

### Проблема: Не могу активировать venv
```bash
# Убедитесь, что venv создан
ls venv/  # Должны быть папки bin, lib, include

# Если venv не создан
python3 -m venv venv

# Активировать
source venv/bin/activate
```

## 🔒 .gitignore

Папка `venv/` уже добавлена в `.gitignore` и не будет отслеживаться Git.
Каждый разработчик создаёт своё локальное окружение.

---
