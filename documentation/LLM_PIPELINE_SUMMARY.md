# 🤖 Резюме: Пайплайн LLM-перевода

## Пайплайн

```
.rpy файлы
    ↓
[llm_translate_prepare.py]
    ↓
JSON файлы
    ↓
[llm_translate.py] + LLM API
    ↓
JSON с переводами
    ↓
[llm_translate_apply.py]
    ↓
Обновленные .rpy файлы
    ↓
[smart_pack_translations.py]
    ↓
game/tl/ru/ (игровые файлы)
```

---

## 🚀 Использование

### Быстрый старт

```bash
cd tools
./llm_batch_translate.sh

# 3. Тестировать
cd .. && ./Ravager.sh
```

### Пошаговая обработка

```bash
cd tools

# Шаг 1: Подготовка
python3 llm_translate_prepare.py

# Шаг 2: Перевод
python3 llm_translate.py \
    --input ../temp_files/llm_json/c1_ru.json \
    --output ../temp_files/llm_json/c1_ru_translated.json

# Шаг 3: Применение
python3 llm_translate_apply.py

# Шаг 4: Упаковка
python3 smart_pack_translations.py
```
