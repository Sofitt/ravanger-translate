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
  - Автоматическое заполнение пустых переводов оригиналом
  - Объединение переводов без дубликатов

### 🤖 LLM-перевод (автоматизация):
- **`llm_translate_prepare.py`** - Подготовка .rpy → JSON для LLM
- **`llm_translate.py`** - Перевод через локальную LLM с валидацией
- **`llm_translate_apply.py`** - Применение переводов JSON → .rpy
- **`llm_batch_translate.sh`** - ⭐ Полный автоматический пайплайн
- **`LLM_TOOLS_README.md`** - Подробная документация по LLM-переводу

### 📋 Шаблоны:
- **`common_translations.json`** - Шаблон базовых переводов

## 🚀 Быстрый старт:

### Первоначальная настройка:
```bash
# Создать и активировать виртуальное окружение
cd ..
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### Использование (всегда активируйте venv):
```bash
# Активировать окружение
source venv/bin/activate

# 1. Извлечь .rpy файлы из архивов игры (первый раз)
cd tools && python3 extract_scripts.py

# 2. Извлечь переводимые строки из .rpy файлов
python3 extract_dialogue_only.py

# 3. Разбить на модули для удобного перевода
python3 split_translation.py

# 4. Упаковать готовые переводы в игру
python3 smart_pack_translations.py

# 5. Проверить прогресс перевода
python3 translation_helper.py
```

## 🤖 LLM-перевод (автоматизация):

### Для автоматического перевода через локальную LLM:

```bash
# Полный автоматический пайплайн
./llm_batch_translate.sh

# Или вручную по шагам:
# 1. Подготовить данные для LLM
python3 llm_translate_prepare.py

# 2. Перевести через LLM API
python3 llm_translate.py \
    --input ../temp_files/llm_json/c1_ru.json \
    --output ../temp_files/llm_json/c1_ru_translated.json \
    --api-url http://localhost:8080/v1/chat/completions

# 3. Применить переводы обратно
python3 llm_translate_apply.py

# 4. Упаковать в игру
python3 smart_pack_translations.py
```

**📚 Подробнее:** см. `LLM_TOOLS_README.md` и `../documentation/LLM_TRANSLATION_GUIDE.md`
