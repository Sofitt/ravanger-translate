# 🛠️ Инструменты для перевода

## Основные инструменты:

### 📊 Извлечение и анализ:
- **`extract_dialogue_only.py`** - Извлекает только диалоги из игры (ОСНОВНОЙ)
- **`translation_helper.py`** - Анализ прогресса и статистика

### 🔄 Обработка переводов:
- **`split_translation.py`** - Разделяет переводы на модули
- **`apply_translations.py`** - Применяет переводы к модулям
- **`fix_duplicates.py`** - Исправляет дубликаты в файлах

### 📦 Упаковка:
- **`smart_pack_translations.py`** - ⭐ **ГЛАВНЫЙ ИНСТРУМЕНТ** - умная упаковка переводов

### 📋 Шаблоны:
- **`common_translations.json`** - Шаблон базовых переводов

## 🚀 Быстрый старт:

```bash
# Основная команда для упаковки переводов
python3 tools/smart_pack_translations.py

# Анализ прогресса
python3 tools/translation_helper.py

# Извлечение новых диалогов (если обновилась игра)
python3 tools/extract_dialogue_only.py

# Разбивка диалогов на модули для перевода
python3 tools/split_translation.py
```
