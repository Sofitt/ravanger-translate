# 🛠️ Инструменты для перевода

## Основные инструменты:

### 📊 Извлечение и анализ:
- **`extract_dialogue_only.py`** - Извлекает только диалоги из игры
- **`extract_strings.py`** - Базовое извлечение строк
- **`extract_strings_improved.py`** - Улучшенное извлечение
- **`translation_helper.py`** - Анализ прогресса и статистика

### 🔄 Обработка переводов:
- **`split_translation.py`** - Разделяет переводы на модули
- **`apply_translations.py`** - Применяет переводы к модулям
- **`fix_duplicates.py`** - Исправляет дубликаты в файлах

### 📦 Упаковка:
- **`smart_pack_translations.py`** - ⭐ **ГЛАВНЫЙ ИНСТРУМЕНТ** - умная упаковка
- **`pack_translations.py`** - Базовая упаковка (устарел)

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
```
