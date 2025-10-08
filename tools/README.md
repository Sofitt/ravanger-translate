# 🛠️ Инструменты для перевода

## Основные инструменты:

### 📊 Извлечение и анализ:
- **`extract_scripts.py`** - ⭐ Извлекает .rpy файлы из архивов игры
- **`extract_dialogue_only.py`** - Извлекает диалоги и переводимые строки
- **`translation_helper.py`** - Анализ прогресса и статистика

### 🔄 Обработка переводов:
- **`split_translation.py`** - Разделяет переводы на модули

### 📦 Упаковка:
- **`smart_pack_translations.py`** - ⭐ **ГЛАВНЫЙ ИНСТРУМЕНТ** - умная упаковка переводов

### 📋 Шаблоны:
- **`common_translations.json`** - Шаблон базовых переводов

## 🚀 Быстрый старт:

```bash
# 1. Извлечь .rpy файлы из архивов игры (первый раз)
cd tools && python3 extract_scripts.py

# 2. Извлечь переводимые строки из .rpy файлов
cd tools && python3 extract_dialogue_only.py

# 3. Разбить на модули для удобного перевода
cd tools && python3 split_translation.py

# 4. Упаковать готовые переводы в игру
cd tools && python3 smart_pack_translations.py

# 5. Проверить прогресс перевода
cd tools && python3 translation_helper.py
```
