# 🤖 Быстрый старт: LLM-перевод

## ⚡ За 5 минут

### 1. Запустите LLM сервер

**Вариант A: llama.cpp**
```bash
./llama-server -m model.gguf -c 4096 --port 8080
```

**Вариант B: Ollama**
```bash
ollama pull llama3
ollama serve
```

### 2. Запустите автоматический перевод

```bash
cd tools

# Полный пайплайн (подготовка + перевод + применение + упаковка)
./llm_batch_translate.sh
```

### 3. Тестируйте

```bash
cd ..
./Ravager.sh
# В игре: Настройки → Язык → Русский
```

---

## 🎯 Настройка API

### llama.cpp (по умолчанию)
```bash
export LLM_API_URL="http://localhost:8080/v1/chat/completions"
export LLM_MODEL="local-model"
```

### Ollama
```bash
export LLM_API_URL="http://localhost:11434/api/chat"
export LLM_MODEL="llama3"
```

### text-generation-webui
```bash
export LLM_API_URL="http://localhost:5000/v1/chat/completions"
export LLM_MODEL="your-model-name"
```

---

## 📊 Частичный перевод

### Перевести один модуль
```bash
cd tools

# Подготовить
python3 llm_translate_prepare.py \
    --module ../translation_modules/c1_ru.rpy \
    --output ../temp_files/c1_ru.json

# Перевести
python3 llm_translate.py \
    --input ../temp_files/c1_ru.json \
    --output ../temp_files/c1_ru_translated.json

# Применить
python3 llm_translate_apply.py \
    --input ../temp_files/c1_ru_translated.json \
    --module ../translation_modules/c1_ru.rpy

# Упаковать
python3 smart_pack_translations.py
```

---

## 🔧 Только подготовка (без перевода)

```bash
cd tools
./llm_batch_translate.sh --prepare-only
```

Результат: JSON файлы в `temp_files/llm_json/`

Теперь можете переводить их через любой инструмент:
- Локальная LLM
- ChatGPT/Claude (экспорт/импорт JSON)
- Ручной перевод

---

## 📚 Полная документация

- **`documentation/LLM_TRANSLATION_GUIDE.md`** - правила перевода
- **`tools/LLM_TOOLS_README.md`** - подробное руководство по инструментам

---

## ⚠️ Важно

1. **Валидация**: Скрипт автоматически проверяет:
   - Сохранность переменных `{var}` и `[var]`
   - Сохранность тегов `{b}`, `{color}`, и т.д.
   - Переносы строк `\n`

2. **Резервные копии**: Создаются автоматически в `temp_files/backups/`

3. **Качество**: Всегда проверяйте первые переводы вручную

---

## 🎮 Рекомендуемые модели

- **Saiga 8B/13B** - лучшее для русского
- **LLaMA 3 8B** - хорошее качество
- **Qwen 7B/14B** - быстрая работа с русским

**Минимум:** 8B параметров для приемлемого качества
